#!/usr/bin/env node
/**
 * test_changelog_entry_gate.mjs — the changelog-entry gate answers the right
 * question about the right files.
 *
 * WHY THIS EXISTS (owner, 2026-09-13: "Getting some red PR's, can you find what is
 * going on make the fix so they don't break again"). `check-changelog-entry.mjs`
 * had no test at all, and it was the commonest cause of a red PR that day — not
 * because it was too strict about the town, but because `tools/dev-smoke-state.json`
 * sits under its watched `tools/` prefix. That file is T-0216's append-only register
 * of smoke RESULTS, and AGENTS.md requires a run to file its readings into it. So a
 * run that did exactly what the contract asks drew a red gate, and the remedy every
 * time was a hand-written `Changelog: none` trailer saying a test result is not a
 * release note. It was written by hand on #1090, #1108, #1126 and #1247 on 09-11,
 * and #1264 and #1269 were red for it again on 09-13 with that file as the ONLY
 * watched path they touched. #1255 looked like the same thing and is not: it
 * changed `tools/smoke_renderer.mjs` as well, so it stays red until it carries an
 * entry or a reason. Case 7 below is that distinction, and it is why the exemption
 * is one path and not a rule about smoke.
 *
 * Exempting the file fixes it once. This is what keeps it fixed, and it holds the
 * gate's OTHER answers at the same time, because an exemption list is exactly the
 * kind of edit that quietly widens:
 *
 *   1. a diff that only files smoke readings is NOT REQUIRED to carry an entry;
 *   2. a real change to the town with no entry still FAILS — the gate still bites,
 *      which is the whole reason it exists (PRs #549 and #619 shipped without one);
 *   3. …and passes with an entry, and passes with a `Changelog: none — why` trailer;
 *   4. `Changelog: none` with NO reason still fails: the reason is the point;
 *   5. tickets/ and docs/ stay exempt;
 *   6. and the BASELINES beside the smoke register are NOT exempt — a moved
 *      baseline is a claim about the town, and only the record of having run a test
 *      is exempt. That is the widening this test exists to refuse.
 *
 * Every case runs the real tool against a real git repository built in a sandbox,
 * because the tool's whole input is `git diff` and `git log` over a commit range —
 * asserting against anything less would be asserting about a mock.
 */
import { mkdtempSync, mkdirSync, rmSync, cpSync, writeFileSync } from 'node:fs';
import { execFileSync, spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

const git = (cwd, ...args) => spawnSync('git', args, {
  cwd,
  encoding: 'utf8',
  env: {
    ...process.env,
    GIT_AUTHOR_NAME: 'test', GIT_AUTHOR_EMAIL: 't@test',
    GIT_COMMITTER_NAME: 'test', GIT_COMMITTER_EMAIL: 't@test',
  },
});

/** A sandbox repo with the tool in place and one base commit. */
function sandbox() {
  const root = mkdtempSync(path.join(tmpdir(), 'clentry-'));
  mkdirSync(path.join(root, 'chicago', '4d', 'tools'), { recursive: true });
  mkdirSync(path.join(root, 'chicago', '4d', 'tickets'), { recursive: true });
  mkdirSync(path.join(root, 'chicago', '4d', 'renderers', 'web', 'js'), { recursive: true });
  cpSync(path.join(HERE, 'check-changelog-entry.mjs'),
    path.join(root, 'chicago', '4d', 'tools', 'check-changelog-entry.mjs'));
  const w = (rel, text) => {
    mkdirSync(path.dirname(path.join(root, rel)), { recursive: true });
    writeFileSync(path.join(root, rel), text);
  };
  w('chicago/4d/renderers/web/js/changelog.js', 'export const CHANGELOG = [\n];\n');
  w('chicago/4d/data/town.json', '{"roofs": 1}\n');
  w('chicago/4d/tools/dev-smoke-state.json', '{"readings": []}\n');
  w('chicago/4d/tools/research_spend_baseline.json', '{"read": 1}\n');
  w('chicago/4d/tickets/QUEUE.md', '# QUEUE\n');
  git(root, 'init', '-q', '-b', 'main');
  git(root, 'add', '-A');
  git(root, 'commit', '-q', '-m', 'base');
  return { root, w, base: git(root, 'rev-parse', 'HEAD').stdout.trim() };
}

/** Commit a change and ask the gate about it. Returns { code, out }. */
function ask(s, files, message) {
  for (const [rel, text] of Object.entries(files)) s.w(rel, text);
  git(s.root, 'add', '-A');
  git(s.root, 'commit', '-q', '-m', message);
  const head = git(s.root, 'rev-parse', 'HEAD').stdout.trim();
  const r = spawnSync('node',
    [path.join(s.root, 'chicago', '4d', 'tools', 'check-changelog-entry.mjs'), s.base, head],
    { cwd: s.root, encoding: 'utf8' });
  return { code: r.status, out: `${r.stdout ?? ''}${r.stderr ?? ''}` };
}

console.log('changelog-entry gate');
const boxes = [];
const box = () => { const s = sandbox(); boxes.push(s.root); return s; };

/* 1. THE REGRESSION: filing smoke readings needs no changelog entry. */
{
  const r = ask(box(), { 'chicago/4d/tools/dev-smoke-state.json': '{"readings": [{"stage": 7}]}\n' },
    'file the smoke readings this run took');
  check('a diff that only files smoke readings is not required to carry an entry',
    r.code === 0, r.out.trim().split('\n')[0]);
  check('…and the gate says so by name, rather than passing silently',
    /not required/.test(r.out));
}

/* 2. THE GATE STILL BITES. A real change with no entry fails. */
{
  const r = ask(box(), { 'chicago/4d/data/town.json': '{"roofs": 2}\n' },
    'move a roof and say nothing about it');
  check('a real change to the town with NO entry still fails', r.code !== 0, `exit ${r.code}`);
  check('…and names the file it is unhappy about',
    /data\/town\.json/.test(r.out));
}

/* 3. …and passes the two legitimate ways. */
{
  const r = ask(box(), {
    'chicago/4d/data/town.json': '{"roofs": 2}\n',
    'chicago/4d/renderers/web/js/changelog.js': 'export const CHANGELOG = [\n  {},\n];\n',
  }, 'move a roof and write the entry');
  check('a real change WITH an entry passes', r.code === 0, r.out.trim().split('\n')[0]);
}
{
  const r = ask(box(), { 'chicago/4d/data/town.json': '{"roofs": 2}\n' },
    'move a roof\n\nChangelog: none — rebuilt bytes, nothing a visitor sees');
  check('a real change with a reasoned opt-out trailer passes', r.code === 0);
  check('…and the reason is echoed, so it is on the record',
    /opted out/.test(r.out) && /rebuilt bytes/.test(r.out));
}

/* 4. The opt-out needs a reason. */
{
  const r = ask(box(), { 'chicago/4d/data/town.json': '{"roofs": 2}\n' },
    'move a roof\n\nChangelog: none');
  check('`Changelog: none` with no reason after it is refused', r.code !== 0, `exit ${r.code}`);
}

/* 5. tickets/ and docs/ stay exempt. */
{
  const r = ask(box(), { 'chicago/4d/tickets/QUEUE.md': '# QUEUE\nT-0001 — a line\n' },
    're-rank the queue');
  check('a tickets/ change is still exempt', r.code === 0);
}

/* 6. THE WIDENING THIS REFUSES: a baseline is not a smoke reading. */
{
  const r = ask(box(), { 'chicago/4d/tools/research_spend_baseline.json': '{"read": 2}\n' },
    'move the research baseline');
  check('a moved BASELINE under tools/ is NOT exempt', r.code !== 0, `exit ${r.code}`);
  check('…and it is named, not swept in with the smoke register',
    /research_spend_baseline\.json/.test(r.out));
}

/* 7. Both together: readings beside a real change still need the entry. */
{
  const r = ask(box(), {
    'chicago/4d/tools/dev-smoke-state.json': '{"readings": [{"stage": 7}]}\n',
    'chicago/4d/data/town.json': '{"roofs": 3}\n',
  }, 'move a roof and file the readings for it');
  check('readings filed BESIDE a real change do not excuse the entry', r.code !== 0, `exit ${r.code}`);
  check('…and only the real file is named', /town\.json/.test(r.out)
    && !/dev-smoke-state/.test(r.out));
}

for (const b of boxes) rmSync(b, { recursive: true, force: true });

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);
