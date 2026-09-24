#!/usr/bin/env node
/**
 * audit_manifest_coverage.mjs — T-1282. A GATED WRITER BELONGS IN THE MANIFEST.
 *
 * `tools/derived_manifest.json` is what lets pr-lap.sh clear a merge conflict by
 * REBUILDING a generated file instead of picking a side. A tool that check.sh gates with
 * `--check`, and that can also WRITE, is by definition a tool whose output is derived —
 * so if it is not in the manifest, `rederive.mjs --run` never runs it, the lap leaves the
 * branch stale, and the gate goes red with no automated remedy.
 *
 * WHY THIS IS A GATE AND NOT A NOTE (owner, 2026-09-18: "add a note to things to say if
 * you add a writer it should be in that manifest, right?"). A note is what we already had,
 * in the manifest's own preamble, and it did not hold: on the night of 2026-09-17 FOUR
 * separate hand-fixes were needed on this one gap, every one of them a gated writer the
 * manifest had never heard of — derive_resident_roles.py (household cards, hit on four
 * merges), location_spend.py, profile_population_1835.py and model_town_1835.py. Each cost
 * a red PR, a diagnosis and a hand rebuild. The rule is only worth anything if adding a
 * writer and forgetting the manifest FAILS.
 *
 * NOT EVERY GATED WRITER MAY BE LISTED, which is why the answer is an exemption list and
 * not an auto-add. `_must_reproduce` in the manifest names the case: a tool can pass
 * `--check` and still not rebuild to itself, and listing it would let the lap overwrite
 * real content — crosswalk_census_1840_heads.py is the standing example, green on --check
 * while --build rewrote 137 lines. So a tool is either IN the manifest or in
 * `_not_derivable` below WITH A REASON somebody wrote.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const APP = path.resolve(HERE, '..');
const read = (p) => readFileSync(path.join(APP, p), 'utf8');

/**
 * T-1302. THE INVENTORY REPLACED THE PATTERN, BECAUSE NO PATTERN WAS RIGHT.
 *
 * This audit used to answer "can this tool write?" by matching its SOURCE. Every version
 * of that test is wrong, and each was measured on 2026-09-18 against the real tree:
 *
 *   anchored to a line start (as shipped)  found  0 unlisted writers
 *   widened bluntly                        found 59 — but EIGHT of those declare no write
 *                                                mode at all and matched the string
 *                                                `--build` inside their own prose;
 *                                                carry_stage_blocks.py has only --check
 *   matching a DECLARED flag only          found 52 — and misses read_fergus_1839.py,
 *                                                which has no --build, and WRITES BY
 *                                                DEFAULT when the argument is neither
 *                                                --check nor --self-test
 *
 * A tool's write mode is sometimes its default branch, so no reading of the source can
 * answer the question. Behaviour can: run it on a clean tree and ask git what moved. That
 * is far too slow for a per-commit gate — and it does not need to run per commit, because
 * the answer only changes when a TOOL changes. So the measurement is committed, with a
 * date beside every row, in tools/writer_inventory.json, and this gate holds the tree to
 * it: a gated tool with no measured row fails here. That is what stops a new writer
 * arriving unmeasured, which is the hole the ticket was filed for.
 */
const check = read('tools/check.sh');
const manifest = read('tools/derived_manifest.json');
const inventory = JSON.parse(read('tools/writer_inventory.json'));
const INV = inventory.tools;

/**
 * T-1453. AN UNKNOWN PLACEMENT IS A FAILURE, NOT A ROW THAT VANISHES.
 *
 * The legal placements ARE the keys of `_placement`, so the vocabulary and the prose that
 * explains it cannot drift apart: adding a bucket means documenting it in the same edit.
 *
 * Before this, a row carrying anything else was counted by no bucket and refused by
 * nothing, and the summary printed a total with a breakdown that did not reach it — three
 * rows short, reading OK. All three said `reproduces`, which is an OUTCOME of measuring a
 * tool and not a place to put it; the placement that follows from reproducing is `pending`.
 * The audit's own guidance handed that word back (see the outcome table below), so the
 * conflation came from here.
 */
const LEGAL = Object.keys(inventory._placement);
const OUTCOME_TO_PLACEMENT = { reproduces: 'pending', not_derivable: 'not_derivable', not_a_writer: 'not_a_writer' };

// A tool is LISTED when a step RUNS it, not when a note MENTIONS it. The substring test
// this replaces read `tools/read_newberry_index.py` out of another step's prose and
// called it listed — the one tool the old exemption list existed to keep out.
const manifestTools = new Set(
  JSON.parse(manifest).steps.flatMap((step) => step.command
    .filter((a) => /^tools\/[a-z0-9_]+\.py$/.test(a))
    .map((a) => a.replace(/^tools\//, ''))));

const gated = new Set([...check.matchAll(/python3 tools\/([a-z0-9_]+\.py) --check/g)].map((m) => m[1]));

const unmeasured = [];
const disagree = [];
const illegal = [];
const unreasoned = [];
for (const tool of [...gated].sort()) {
  const row = INV[tool];
  if (!row) { unmeasured.push(tool); continue; }
  if (!LEGAL.includes(row.placement)) {
    const meant = OUTCOME_TO_PLACEMENT[row.placement];
    illegal.push(`${tool} — placement '${row.placement}' is not a placement`
      + (meant ? `; it is the OUTCOME of measuring the tool, and the placement that follows from it is '${meant}'` : ''));
    continue;
  }
  // A tool outside the manifest owes the next run a sentence it can act on. `pending` says
  // only "not placed yet"; `placed` says WHY, and what has to be settled before it can be.
  if (row.placement === 'pending' && !String(row.placed || '').trim()) unreasoned.push(tool);
  const listed = manifestTools.has(tool);
  if (row.placement === 'manifest' && !listed) {
    disagree.push(`${tool} — the inventory says 'manifest'; the manifest does not run it`);
  } else if (row.placement !== 'manifest' && listed) {
    disagree.push(`${tool} — the manifest runs it; the inventory says '${row.placement}'`);
  }
}

if (unmeasured.length || disagree.length || illegal.length || unreasoned.length) {
  console.error('manifest coverage: MISSING.\n');
  if (unmeasured.length) {
    console.error(`${unmeasured.length} tool(s) are gated with --check and have NO measured row`);
    console.error('in tools/writer_inventory.json:\n');
    for (const t of unmeasured) console.error(`  tools/${t}`);
    console.error('\nMEASURE IT; DO NOT READ ITS SOURCE — the note above says why that cannot');
    console.error('work. Run its write mode on a clean tree, or run it BARE if it declares no');
    console.error('flag, and record what git says moved:');
    console.error('  wrote its own outputs and changed no committed byte  -> reproduces');
    console.error('  changed a committed byte                             -> not_derivable, WITH THE NUMBER');
    console.error('  wrote nothing, and it HAS a write flag               -> perturb it before deciding');
    console.error('  wrote nothing, run bare                              -> not_a_writer\n');
    console.error('THAT IS THE OUTCOME, AND TWO OF THOSE WORDS ARE NOT PLACEMENTS. Write the');
    console.error('PLACEMENT into the row:\n');
    console.error('  reproduces     -> placement `pending`, WITH a `placed` field saying what has');
    console.error('                    to be settled before it can join the manifest\'s order');
    console.error('  not_derivable  -> placement `not_derivable`, with the number in `finding`');
    console.error('  not_a_writer   -> placement `not_a_writer`\n');
  }
  if (illegal.length) {
    console.error(`${illegal.length} row(s) in tools/writer_inventory.json carry a placement this`);
    console.error('audit does not know, so no bucket counts them and no line reports them:\n');
    for (const d of illegal) console.error(`  ${d}`);
    console.error(`\nThe legal placements are exactly the keys of \`_placement\` in that file: ${LEGAL.join(', ')}.`);
    console.error('Adding a fifth means documenting it there in the same edit.\n');
  }
  if (unreasoned.length) {
    console.error(`${unreasoned.length} tool(s) sit OUTSIDE the manifest with no written reason:\n`);
    for (const t of unreasoned) console.error(`  tools/${t}`);
    console.error('\nA `pending` row needs a `placed` field. `pending` says only that the tool is not');
    console.error('in the manifest; `placed` says why, and what a run has to settle to place it —');
    console.error('which stages write what it reads, or which pass owns its slot. Without it the');
    console.error('next run rediscovers the ordering by hand: driving #1560 green cost three gate');
    console.error('cycles to learn that complete_inwindow_trades.py runs BEFORE rederive.mjs --run.\n');
  }
  if (disagree.length) {
    console.error('The inventory and the manifest disagree:\n');
    for (const d of disagree) console.error(`  ${d}`);
    console.error('');
  }
  process.exit(1);
}

/**
 * T-1453. THE SUM IS AN ASSERTION, NOT A SET OF NUMBERS PRINTED NEAR EACH OTHER.
 *
 * This summary counted its buckets over the WHOLE inventory while printing `gated.size` as
 * the total, and nothing held the two to each other. That is how it came to say "208 gated
 * tool(s), every one measured" above 152 + 17 + 15 + 22 = 206, and later 218 above 215.
 *
 * Two things now hold it. The buckets are counted over the GATED set — the same set the
 * total measures — and the breakdown is built from ONE table, so the numbers that are added
 * up are the numbers that get printed. The refusal above means a gated tool always lands in
 * a legal bucket, so the only way the sum can miss one now is a fifth placement documented
 * in `_placement` and never given a line here; that is what REPORTED is checked against.
 */
const REPORTED = {
  manifest: 'in the manifest',
  pending: 'measured to reproduce and not yet placed',
  not_derivable: 'cannot rebuild, each with its number',
  not_a_writer: 'write nothing',
};
const unreported = LEGAL.filter((p) => !(p in REPORTED));
if (unreported.length) {
  console.error('manifest coverage: A BUCKET NOBODY PRINTS.\n');
  console.error(`  _placement documents ${unreported.map((p) => `'${p}'`).join(', ')}, and this summary has no line for it,`);
  console.error('  so every tool placed there would be counted by nothing. Give it a line in');
  console.error('  REPORTED, in tools/audit_manifest_coverage.mjs, in the same edit.\n');
  process.exit(1);
}

const counts = Object.fromEntries(Object.keys(REPORTED).map((p) => [p, [...gated].filter((t) => INV[t].placement === p).length]));
const summed = Object.values(counts).reduce((n, c) => n + c, 0);
if (summed !== gated.size) {
  console.error('manifest coverage: THE BREAKDOWN DOES NOT REACH THE TOTAL.\n');
  console.error(`  ${gated.size} gated tool(s), and the buckets account for ${summed}:\n`);
  for (const [p, c] of Object.entries(counts)) console.error(`    ${String(c).padStart(4)}  ${p}`);
  console.error(`\n  ${Math.abs(gated.size - summed)} unaccounted for. A tool counted by no bucket is a tool this`);
  console.error('  gate is not watching, so the disagreement is the failure and not a rounding.\n');
  process.exit(1);
}
console.log(`manifest coverage: OK — ${gated.size} gated tool(s), every one measured and counted once.`);
console.log(`  ${counts.manifest} ${REPORTED.manifest} · ${counts.pending} ${REPORTED.pending}`);
console.log(`  ${counts.not_derivable} ${REPORTED.not_derivable} · ${counts.not_a_writer} ${REPORTED.not_a_writer}`);
console.log(`  ${Object.values(counts).join(' + ')} = ${summed}, which is the total above.`);
if (counts.pending) {
  console.log('  The pending ones are recorded, not hidden. Ordering is its own measured pass:');
  console.log('  on #1452 three reconstruction stages OSCILLATED until they sat in the right');
  console.log('  slot, so these cannot be appended to the manifest blind (T-1302 batch 2).');
}
