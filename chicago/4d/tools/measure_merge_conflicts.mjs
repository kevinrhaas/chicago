#!/usr/bin/env node
// T-1355 — would taking these files off the PR surface have made any merge clean?
//
//   git fetch origin '+refs/pull/*/head:refs/remotes/pr/*'     # once, first
//   node tools/measure_merge_conflicts.mjs                    # the four research reports
//   node tools/measure_merge_conflicts.mjs <path…>             # any other candidate set
//
// WHAT IT READS. Every merge commit on a pull request's head that `dev` does not
// contain — the lap's `Lap onto dev`, and a run's own merge of `dev` into its branch.
// Everything here squash-merges, so those merges live ONLY on the PR heads, and
// GitHub keeps `refs/pull/N/head` after the branch is deleted. Each merge is replayed
// with `git merge-tree` on its own two parents, so the conflicted set is the one git
// actually faced, not a guess from which files two commits both touched.
//
// WHAT IT ANSWERS. Untracking a file removes its conflicts and nobody else's. So the
// number that decides whether a candidate set is worth taking off the surface is the
// merges where it was the ONLY conflict — those, and only those, it would have turned
// clean. Each merge is put in one row:
//
//   clean               no conflict at all
//   only the candidates every conflicted file is a candidate: untracking would clear it
//   + derived           candidates and other manifest-owned files: the lap clears it either way
//   + driver files      candidates beside changelog.js / dev-smoke-state.json, which have
//                       local merge drivers that GitHub's server-side merge does not run
//   + hand-authored     candidates beside a file no tool rebuilds: a run has to resolve it
//   no candidate        the candidates were not in it
//
// Read-only. It writes nothing and fetches nothing, and it says so when there is
// nothing to read rather than printing a row of zeros.
import { execFileSync } from 'node:child_process';

const git = (...a) => execFileSync('git', a, { encoding: 'utf8', maxBuffer: 1 << 28 });

const FOUR = [
  'chicago/4d/docs/RESEARCH/research-spend-ledger-2026-09-15.md',
  'chicago/4d/data/research/research_spend_ledger.json.gz',
  'chicago/4d/docs/RESEARCH/research-signoff-2026-09.md',
  'chicago/4d/docs/RESEARCH/research-closing-audit-2026-09.md',
];
const DRIVER = new Set(['chicago/4d/renderers/web/js/changelog.js', 'chicago/4d/tools/dev-smoke-state.json']);
const BASE = process.env.MEASURE_BASE || 'origin/dev';

const args = process.argv.slice(2);
const CAND = new Set(args.length ? args : FOUR);
const manifest = JSON.parse(git('show', `${BASE}:chicago/4d/tools/derived_manifest.json`));
const DERIVED = new Set(manifest.steps.flatMap((s) => s.resolves ?? []));

const heads = git('for-each-ref', '--format=%(refname)', 'refs/remotes/pr').trim();
if (!heads) {
  console.error("no PR heads to read — run: git fetch origin '+refs/pull/*/head:refs/remotes/pr/*'");
  process.exit(2);
}
const merges = git('log', '--merges', '--source', '--format=%H %P|%cI|%S',
  '--remotes=pr', `^${BASE}`, '^origin/main').split('\n').filter(Boolean);

const rows = ['clean', 'only the candidates', '+ derived', '+ driver files', '+ hand-authored', 'no candidate'];
const tally = Object.fromEntries(rows.map((r) => [r, { merges: 0, prs: new Set() }]));
const perFile = Object.fromEntries([...CAND].map((f) => [f, 0]));
let first = null, last = null;

for (const line of merges) {
  const [ids, when, src] = line.split('|');
  const [, p1, p2, ...more] = ids.split(' ');
  if (!p2 || more.length) continue; // octopus merges are not laps
  let out = '';
  try { out = git('merge-tree', '--write-tree', '--name-only', '--no-messages', p1, p2); }
  catch (e) { out = e.stdout ?? ''; } // exit 1 is "conflicted", and the list is on stdout
  const files = out.trim().split('\n').slice(1).filter(Boolean);
  const hit = files.filter((f) => CAND.has(f));
  const rest = files.filter((f) => !CAND.has(f));
  for (const f of hit) perFile[f]++;
  const row = !files.length ? 'clean'
    : !hit.length ? 'no candidate'
    : !rest.length ? 'only the candidates'
    : rest.some((f) => !DERIVED.has(f) && !DRIVER.has(f)) ? '+ hand-authored'
    : rest.some((f) => DRIVER.has(f)) ? '+ driver files'
    : '+ derived';
  tally[row].merges++;
  tally[row].prs.add(src.split('/').pop());
  if (!first || when < first) first = when;
  if (!last || when > last) last = when;
}

const total = rows.reduce((n, r) => n + tally[r].merges, 0);
console.log(`${total} merge(s) on ${heads.split('\n').length} PR head(s), ${first} → ${last}, against ${BASE}'s manifest`);
for (const r of rows) console.log(`  ${r.padEnd(20)} ${String(tally[r].merges).padStart(5)} merge(s)  ${String(tally[r].prs.size).padStart(4)} PR(s)`);
console.log('per candidate (merges it conflicted in):');
for (const [f, n] of Object.entries(perFile)) console.log(`  ${String(n).padStart(5)}  ${f}`);
const freed = tally['only the candidates'].merges;
console.log(`untracking the candidates would have made ${freed} of ${total} merge(s) clean.`);
