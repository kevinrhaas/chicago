#!/usr/bin/env node
/**
 * The queue-order gate's assertions, and proof they fire.
 *
 * The cases are the three times the ranking was actually lost, not invented ones:
 * a branch cut before a re-rank (#801, which took the file from 415 lines back to
 * a 2026-08-30 revision), a band stripped and its tickets left at line 416 (#909),
 * and the same-day case that a date comparison would wave through — two re-ranks
 * happened on 2026-09-05 alone.
 */
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, mkdirSync, rmSync, copyFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { ledgerEntries } from './check_queue_order.mjs';

let pass = 0; let fail = 0;
const ok = (cond, what) => {
  if (cond) { pass++; console.log(`  ok    ${what}`); }
  else { fail++; console.log(`  FAIL  ${what}`); }
};

const HERE = path.dirname(new URL(import.meta.url).pathname);
const GATE = path.join(HERE, 'check_queue_order.mjs');

const HEAD = '# QUEUE — top is next.\n#\n';
const ledger = (...entries) => `${HEAD}# RE-RANK LEDGER — newest first\n`
  + entries.map((e) => `#   ${e}\n`).join('')
  + '#               a continuation line that is not its own entry\n#\n';
const tickets = (...ids) => `${ids.map((i) => `T-0${i} — label ${i}`).join('\n')}\n`;

/**
 * Build a throwaway repo whose `origin/dev` carries `baseQueue`, check out a
 * branch carrying `branchQueue`, and run the gate there. This exercises the real
 * `git show origin/dev:<path>` path rather than stubbing it, because the thing
 * most likely to break quietly is the lookup, not the comparison.
 */
function run(baseQueue, branchQueue, baseArchive = null, branchArchive = null) {
  const dir = mkdtempSync(path.join(tmpdir(), 'qo-'));
  const rel = 'chicago/4d/tickets';
  mkdirSync(path.join(dir, rel), { recursive: true });
  mkdirSync(path.join(dir, 'chicago/4d/tools'), { recursive: true });
  // The gate resolves QUEUE.md from its OWN location, so it has to live inside the
  // sandbox repo — running the real one with a different cwd would read the real
  // queue and quietly test nothing. (That is how the first version of this file
  // passed a case it was not exercising.)
  copyFileSync(GATE, path.join(dir, 'chicago/4d/tools/check_queue_order.mjs'));
  const gate = path.join(dir, 'chicago/4d/tools/check_queue_order.mjs');
  const git = (...a) => spawnSync('git', ['-C', dir, ...a], { encoding: 'utf8' });
  const put = (body) => writeFileSync(path.join(dir, rel, 'QUEUE.md'), body);

  git('init', '-q', '-b', 'dev');
  git('config', 'user.email', 't@t'); git('config', 'user.name', 't');
  put(baseQueue);
  if (baseArchive !== null) writeFileSync(path.join(dir, rel, 'QUEUE_ORDER.md'), baseArchive);
  git('add', '-A'); git('commit', '-qm', 'base');
  // A real remote-tracking ref, so the gate's own lookup is what is tested.
  git('update-ref', 'refs/remotes/origin/dev', 'HEAD');
  git('checkout', '-q', '-b', 'branch');
  put(branchQueue);
  if (branchArchive !== null) writeFileSync(path.join(dir, rel, 'QUEUE_ORDER.md'), branchArchive);
  git('add', '-A'); git('commit', '-qm', 'branch');

  const r = spawnSync('node', [gate], {
    cwd: path.join(dir, 'chicago/4d'), encoding: 'utf8',
  });
  rmSync(dir, { recursive: true, force: true });
  return { code: r.status, out: `${r.stdout}${r.stderr}` };
}

console.log('\nthe gate');
{
  const same = ledger('2026-09-05  "Rank T-0727"', '2026-09-04  research first') + tickets(1, 2);
  const r = run(same, same);
  ok(r.code === 0, 'a branch carrying the base\'s ledger passes');
}
{
  // #801 exactly: a branch cut before a re-rank, merged after it.
  const base = ledger('2026-09-05  "Rank T-0727"', '2026-09-04  research first') + tickets(1, 2);
  const stale = ledger('2026-09-04  research first') + tickets(1, 2);
  const r = run(base, stale);
  ok(r.code === 1, 'a branch cut BEFORE a re-rank is refused');
  ok(/Rank T-0727/.test(r.out), '…and the refusal names the instruction that was lost');
  ok(/Restore the missing base entries/.test(r.out), '…and says to restore the base decisions');
}
{
  // The case a date comparison waves through: two re-ranks share one date, and the
  // branch dropped one of them. Both files' newest date is 2026-09-05.
  const base = ledger('2026-09-05  "Rank T-0727"', '2026-09-05  pace sliders') + tickets(1);
  const half = ledger('2026-09-05  pace sliders') + tickets(1);
  const r = run(base, half);
  ok(r.code === 1, 'dropping ONE of two same-day re-ranks is refused — a date check would pass it');
}
{
  const base = ledger('2026-09-04  research first') + tickets(1);
  const ahead = ledger('2026-09-06  a new instruction', '2026-09-04  research first') + tickets(1);
  const r = run(base, ahead);
  ok(r.code === 0, 'a branch that ADDS a re-rank passes — the gate never judges a ranking');
  ok(/adds 1/.test(r.out), '…and says so');
}
{
  const base = ledger('2026-09-04  research first') + tickets(1);
  const gone = `${HEAD}${tickets(1)}`;
  const r = run(base, gone);
  ok(r.code === 1, 'a branch that lost the LEDGER HEADER entirely is refused');
}
{
  const noLedgerBase = `${HEAD}${tickets(1)}`;
  const withLedger = ledger('2026-09-04  research first') + tickets(1);
  const r = run(noLedgerBase, withLedger);
  ok(r.code === 0, 'a base with no ledger cannot fail a branch that has one');
}
{
  const base = ledger('2026-09-04  research first') + tickets(1);
  const clean = `${HEAD}${tickets(1)}`;
  const archive = ledger('2026-09-17  clean queue', '2026-09-04  research first');
  const r = run(base, clean, null, archive);
  ok(r.code === 0, 'the legacy ledger can move to a compact companion file');
  const next = run(clean, clean, archive, ledger('2026-09-17  clean queue'));
  ok(next.code === 1, 'a later branch dropping an archived decision is refused');
}

console.log('\nthe parser, since everything above rests on it');
{
  const e = ledgerEntries(ledger('2026-09-05  one', '2026-09-04  two'));
  ok(e.length === 2, 'continuation lines are not counted as entries');
  ok(e[0].startsWith('2026-09-05'), '…and an entry keeps its date and instruction');
}
{
  ok(ledgerEntries('# QUEUE\nT-0001 — x\n') === null,
    'a file with no ledger header parses as null, not as an empty ledger');
}
{
  // The ledger ends at the first non-comment line: a ticket that happens to be
  // dated must never be read as a re-rank.
  const text = '# RE-RANK LEDGER\n#   2026-09-05  real\nT-0001 — 2026-09-06 not a ledger entry\n';
  ok(ledgerEntries(text).length === 1, 'a dated TICKET line below the ledger is not an entry');
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
