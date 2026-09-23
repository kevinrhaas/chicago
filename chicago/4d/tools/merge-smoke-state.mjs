#!/usr/bin/env node
/**
 * The git merge driver for tools/dev-smoke-state.json — the smoke ledger.
 *
 *   result = OURS' readings, plus every reading THEIRS has that ours does not.
 *
 * WHY THIS FILE GETS ITS OWN DRIVER RATHER THAN merge-generated's (T-0831).
 * It sits in the same conflict set as the five build products and looks like one
 * of them, and it is not. Measured before writing this:
 *
 *   - it holds `readings[]` — an APPEND-ONLY register of smoke runs (T-0216),
 *     62 of them on the day this was written;
 *   - its rows carry NO `id`, so T-0820's uniqueness check cannot see it;
 *   - and NO step of check.sh reads it at all.
 *
 * Nothing regenerates it, and nothing would notice if a merge threw half of it
 * away. Keeping ours — the right answer for a build product — would silently
 * discard the other side's readings. #905 resolved one lap by taking dev's side
 * and said so plainly, which is correct for one lap and wrong as a standing rule:
 * a reading is evidence that a gate was run on a tree, and evidence is not
 * regenerable.
 *
 * IT IS NOT `merge=union`, WHICH IS BANNED HERE ON MEASURED GROUNDS. Union is a
 * LINE union and a reading is many lines: the changelog's own history is five
 * silent corruptions in one day (2026-08-15) from exactly that. This works at
 * ENTRY granularity — whole readings, never lines — the way merge-queue.mjs and
 * merge-changelog.mjs do.
 *
 * WHAT COUNTS AS THE SAME READING. Two readings are the same when their JSON is
 * identical with keys sorted. That is deliberately strict: a reading records the
 * tree it ran on (`treeHash`, `commit`, `devCommit`) and when (`takenAt`), so two
 * genuine runs of the same stage differ, and only a merge that carried one
 * reading down both sides produces a true byte-identical pair. Deduplicating
 * those is the one thing this can do without judgement.
 *
 * ORDER. Ours first, in ours' order, then theirs' new readings in theirs' order.
 * The file is append-only and nothing reads it positionally, so this preserves
 * both histories without inventing a global sort over `takenAt` that neither
 * side asked for.
 *
 * IT REFUSES RATHER THAN GUESSES if either side is not the shape it expects — an
 * unparseable file, a missing `readings`, or a `readings` that is not an array.
 * git then leaves ordinary conflict markers for a human, which is the old
 * behaviour and never something worse.
 *
 * Registered by tools/setup-merge-drivers.sh (merge.smokestate.driver), declared
 * in the repo's .gitattributes.
 *
 * Usage (git's driver contract):  merge-smoke-state.mjs %O %A %B %P
 */
import { readFileSync, writeFileSync } from 'node:fs';

const [, , , ours, theirs, placeholder] = process.argv;
const label = placeholder || 'tools/dev-smoke-state.json';

function load(file, side) {
  let doc;
  try {
    doc = JSON.parse(readFileSync(file, 'utf8'));
  } catch (err) {
    console.error(`merge-smoke-state: ${side} does not parse (${err.message}) — refusing, `
      + 'resolve by hand.');
    process.exit(1);
  }
  if (!doc || typeof doc !== 'object' || !Array.isArray(doc.readings)) {
    console.error(`merge-smoke-state: ${side} carries no readings[] array — refusing, `
      + 'resolve by hand. This driver only knows the ledger shape.');
    process.exit(1);
  }
  return doc;
}

const O = load(ours, 'ours');
const T = load(theirs, 'theirs');

/**
 * A canonical form for comparison, sorting keys at EVERY level.
 *
 * Not `JSON.stringify(r, Object.keys(r).sort())`: a replacer ARRAY is applied at
 * every depth, so a nested object whose keys are not in that top-level list has
 * them dropped — and two readings that differ only inside a nested object would
 * then compare equal and one would be discarded as a duplicate. In a driver
 * whose one promise is that no reading is ever dropped, that is the bug that
 * matters.
 */
const canon = (v) => {
  if (Array.isArray(v)) return `[${v.map(canon).join(',')}]`;
  if (v && typeof v === 'object') {
    return `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${canon(v[k])}`).join(',')}}`;
  }
  return JSON.stringify(v) ?? 'null';
};
const key = canon;
const seen = new Set(O.readings.map(key));
const added = T.readings.filter((r) => !seen.has(key(r)));

// Ours' document wins for every field EXCEPT readings — `note` is prose about the
// ledger and is hand-authored, so the branch being merged into keeps its wording
// the same way QUEUE.md keeps ours' order.
const merged = { ...T, ...O, readings: [...O.readings, ...added] };

writeFileSync(ours, `${JSON.stringify(merged, null, 2)}\n`);
console.error(`merge-smoke-state: ${label} reconciled — ${O.readings.length} ours`
  + ` + ${added.length} new from theirs`
  + (T.readings.length - added.length
    ? ` (${T.readings.length - added.length} already held)` : '')
  + ` = ${merged.readings.length} readings. No reading is ever dropped.`);
process.exit(0);
