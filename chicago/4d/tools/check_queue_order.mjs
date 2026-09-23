#!/usr/bin/env node
/**
 * The owner's queue ranking may not go BACKWARDS. Asserted on the branch.
 *
 * WHY THIS EXISTS, and it is T-0817's first ask, written after the ranking was
 * lost for the second time.
 *
 *   2026-09-04  the owner: the queue "got massively reordered ... please put it
 *               back with all of the research items ... at the top". Restored.
 *   2026-09-05  gone again. `origin/dev` at d08fae3b4 carried the restored file
 *               at 415 lines; one merge later — PR #801, a branch cut long
 *               before the re-rank — dev carried 321 lines opening with the
 *               2026-08-30 revision. The whole research band was gone, and the
 *               ledger explaining it with it.
 *   2026-09-05  and a third time, to the drain band (#909): "it has now been
 *               stripped THREE times ... which is how six tickets the owner put
 *               at the top of QUEUE.md came to be sitting at line 416."
 *
 * WHY A GATE AND NOT ONLY A BETTER MERGE DRIVER. `tools/merge-queue.mjs` did its
 * job in the #801 case — it refused — and it was not enough, for a reason T-0817
 * states exactly: **GitHub does not run this repository's merge drivers.** A
 * squash-merge on the server never loads .gitattributes' driver, so the driver
 * protects a local `git merge` and cannot protect the thing that actually lands.
 * A gate can, because `check.sh` IS the required `gate` check on dev's ruleset —
 * so this refuses the merge button itself, which no driver can reach.
 *
 * WHAT IT ASSERTS, and it is deliberately not a judgement about ranking. The
 * The RE-RANK LEDGER in tickets/QUEUE_ORDER.md records one entry per re-rank, each
 * quoting the instruction behind it. A branch cut before a re-rank is missing
 * that entry. So:
 *
 *     every ledger entry on the BASE must still be present on the BRANCH.
 *
 * That is decidable without reading a single ranking, which is the whole point:
 * the gate never asks whether an order is good, only whether the branch has
 * silently dropped a decision the base had already recorded. T-0817's own words:
 * "A PR that carries an older ledger than its base is carrying a regression, and
 * that is decidable without judging any ranking."
 *
 * ENTRIES ARE COMPARED AS A SET, NOT BY DATE. Two re-ranks happened on
 * 2026-09-05 alone, so "is our newest date >= theirs" would have passed a branch
 * that dropped one of them. The identity of an entry is its first line, which
 * carries the date and the instruction.
 *
 * IT SKIPS RATHER THAN GUESSES when there is no base to compare against — a
 * clone with no `origin/dev`, a detached checkout, an offline runner. A gate that
 * fails for want of a network is a gate people learn to bypass.
 */
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT = path.resolve(HERE, '..');
const QUEUE_REL = 'chicago/4d/tickets/QUEUE.md';
const LEDGER_REL = 'chicago/4d/tickets/QUEUE_ORDER.md';

/** The ledger's entries, each keyed by its first line (date + instruction). */
export function ledgerEntries(text) {
  const lines = text.split('\n');
  const start = lines.findIndex((l) => /^#\s*RE-RANK LEDGER\b/.test(l));
  if (start === -1) return null;                 // no ledger at all — reported, not zero
  const out = [];
  for (const line of lines.slice(start + 1)) {
    if (!line.startsWith('#')) break;            // the ledger ends at the first non-comment
    // An entry opens with a date at a fixed indent; its continuations are indented further.
    const m = /^#\s{2,}(\d{4}-\d{2}-\d{2}.*)$/.exec(line);
    if (m) out.push(m[1].replace(/\s+/g, ' ').trim());
  }
  return out;
}

/** Read the separate ledger, falling back to the old queue for pre-migration refs. */
function baseLedger() {
  const ref = process.env.QUEUE_BASE_REF || 'origin/dev';
  for (const file of [LEDGER_REL, QUEUE_REL]) {
    const r = spawnSync('git', ['show', `${ref}:${file}`],
      { cwd: path.resolve(ROOT, '../..'), encoding: 'utf8' });
    if (r.status === 0) return r.stdout;
  }
  return null;
}

function main() {
  let ours;
  try { ours = readFileSync(path.join(ROOT, 'tickets/QUEUE_ORDER.md'), 'utf8'); }
  catch { ours = readFileSync(path.join(ROOT, 'tickets/QUEUE.md'), 'utf8'); }
  const mine = ledgerEntries(ours);

  if (mine === null) {
    console.error('The queue carries no RE-RANK LEDGER in QUEUE_ORDER.md or QUEUE.md.\n'
      + 'Restore the owner\'s ranking decisions from origin/dev before committing.');
    return 1;
  }

  const baseText = baseLedger();
  if (baseText === null) {
    console.log(`queue order: ${mine.length} re-rank(s) recorded `
      + '(no base to compare against — skipped, not failed)');
    return 0;
  }
  const theirs = ledgerEntries(baseText);
  if (theirs === null) {
    console.log(`queue order: ${mine.length} re-rank(s) recorded (the base carries no ledger)`);
    return 0;
  }

  const have = new Set(mine);
  const lost = theirs.filter((e) => !have.has(e));
  if (lost.length) {
    console.error(`THE QUEUE HAS GONE BACKWARDS: ${lost.length} re-rank(s) the base records `
      + 'are missing from this branch.\n');
    for (const e of lost) console.error(`   lost:  ${e.slice(0, 140)}`);
    console.error('\nEach line above is an instruction the owner gave and this branch no longer\n'
      + 'carries — which means its QUEUE.md predates that re-rank and merging it would put\n'
      + 'the old order back on dev. That has happened three times.\n\n'
      + 'Restore the missing base entries before merging. If the base uses the\n'
      + 'separate ledger: git checkout origin/dev -- '
      + `${LEDGER_REL}\n\n`
      + 'Adding the missing lines by hand would satisfy this check and still ship the old\n'
      + 'ranking, which is the failure it exists to catch.');
    return 1;
  }

  const gained = mine.length - theirs.length;
  console.log(`queue order: every one of the base's ${theirs.length} re-rank(s) is still here`
    + (gained > 0 ? `, and this branch adds ${gained}` : ''));
  return 0;
}

if (import.meta.url === `file://${process.argv[1]}`) process.exit(main());
