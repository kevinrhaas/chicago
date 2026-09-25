#!/usr/bin/env node
/**
 * test_pr_lap_checkout.mjs — a lap that cannot check out a branch has to say why.
 *
 * WHY THIS EXISTS (T-1565). The lap's two entry guards said four words each and
 * threw git's stderr away:
 *
 *     git fetch    origin "$BR"        -q 2>/dev/null || { say "  fetch failed";    ... }
 *     git checkout -B "lap/$N" "origin/$BR" -q 2>/dev/null || { say "  checkout failed"; ... }
 *
 * So when #1629 failed here on 2026-09-21 (lap run 35624254338) the run summary
 * carried no reason at all — not which of the two failed, not git's own message,
 * not the ref it could not resolve. T-1521 measured it as a second fault in that
 * same lap run and deliberately did not fold it in: T-1521 fixed the rebuild's
 * missing publish, a different cause with a different fix.
 *
 * Every OTHER refusal in the lap names its step and tails its log — the broken
 * merge, the failed rebuild, the real conflict — which is how T-1521 was found at
 * all. These two were the exception, and an exception in the reporting is where a
 * second fault hides behind the first.
 *
 * THE SCRIPT IS NOT COPIED HERE, AND NEITHER IS GIT. Each case runs the REAL
 * `.github/steward/pr-lap.sh` against a REAL bare remote with REAL git, with only
 * `gh` faked (the PR list is one REST call and this suite is not about GitHub).
 * That is the difference from test_pr_lap_list.mjs, whose fake git stops the lap
 * at the list: the faults here live in git's own refusal messages, so a fake git
 * would be a test of the fake.
 */
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync, rmSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const LAP = path.resolve(HERE, '..', '..', '..', '.github', 'steward', 'pr-lap.sh');

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

const git = (cwd, ...args) => {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8' });
  if (r.status !== 0) throw new Error(`git ${args.join(' ')} in ${cwd}: ${r.stderr}`);
  return (r.stdout || '').trim();
};

/**
 * A bare remote carrying `dev` plus whichever head branches are asked for, and a
 * clone of it. `singleBranch` reproduces a checkout whose remote.origin.fetch is
 * narrow — the fetch then lands in FETCH_HEAD and leaves no remote-tracking ref.
 */
function world({ branches = [], singleBranch = false }) {
  const box = mkdtempSync(path.join(tmpdir(), 'lapco-'));
  const remote = path.join(box, 'remote.git');
  const seed = path.join(box, 'seed');
  git(box, 'init', '--bare', '-b', 'dev', remote);
  git(box, 'init', '-b', 'dev', seed);
  for (const [k, v] of [['user.name', 'test'], ['user.email', 't@e.st']]) git(seed, 'config', k, v);
  // No `merge=` rules: the driver machinery is test_pr_lap_list.mjs's subject,
  // and routing a file to a driver here would only make the lap refuse to start.
  writeFileSync(path.join(seed, '.gitattributes'), '*.bin binary\n');
  writeFileSync(path.join(seed, 'f.txt'), 'dev\n');
  git(seed, 'add', '-A');
  git(seed, 'commit', '-qm', 'dev');
  git(seed, 'remote', 'add', 'origin', remote);
  git(seed, 'push', '-q', 'origin', 'dev');
  for (const b of branches) {
    git(seed, 'checkout', '-q', '-B', b, 'dev');
    writeFileSync(path.join(seed, 'f.txt'), `${b}\n`);
    git(seed, 'commit', '-qam', b);
    git(seed, 'push', '-q', 'origin', b);
    git(seed, 'checkout', '-q', 'dev');
  }
  const work = path.join(box, 'work');
  git(box, 'clone', '-q', ...(singleBranch ? ['--single-branch', '--branch', 'dev'] : []), remote, work);
  return { box, remote, work };
}

/** Run the real lap in `work`, with a fake `gh` answering the PR list. */
function runLap(work, prs) {
  const bin = path.join(work, '..', 'bin');
  mkdirSync(bin, { recursive: true });
  const tsv = prs.map(([n, br]) => `${n}\t${br}`).join('\n') + (prs.length ? '\n' : '');
  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
# REST only: the list is \`gh api\`, for the GraphQL-budget reason pr-lap.sh
# documents at length. Anything else the lap asks of gh, it does not reach here.
case "$*" in
  *pulls*) printf '%b' ${JSON.stringify(tsv)} ;;
esac
exit 0
`);
  chmodSync(path.join(bin, 'gh'), 0o755);
  const r = spawnSync('bash', [LAP], {
    cwd: work,
    encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, GH_TOKEN: 'fake',
           LAP_ONLY: '', LAP_BASE: 'dev', GITHUB_REPOSITORY: 'kevinrhaas/chicago' },
  });
  return { code: r.status, out: `${r.stdout || ''}${r.stderr || ''}` };
}

console.log('pr-lap.sh — a lap that cannot check out a branch has to say why');

/* 1. THE LIKELIEST CAUSE: the head branch was deleted under the lap.
 *
 * `git fetch` answers "couldn't find remote ref", which reads like a transport
 * fault to anybody who does not already know the branch is gone. The lap has to
 * ask the remote and say which it is. */
{
  const w = world({ branches: [] });
  const r = runLap(w.work, [[2001, 'steward/gone']]);
  check('the lap survives a PR whose branch is not there', r.code === 0, `exit ${r.code}`);
  check('…and counts it left alone', /left-alone=1/.test(r.out));
  check('…and says it was the FETCH that failed, naming the branch',
        /FETCH of `steward\/gone` FAILED/.test(r.out));
  check("…and carries git's own message rather than swallowing it",
        /couldn't find remote ref/i.test(r.out));
  check('…and reads as a DELETED branch, not as an unexplained failure',
        /DELETED under the lap/.test(r.out));
  check('…and tells the reader what to do with the PR it named',
        /PR #2001 wants closing/.test(r.out));
  check('…and never prints the old four words',
        !/^\s+fetch failed\s*$/m.test(r.out));
  rmSync(w.box, { recursive: true, force: true });
}

/* 2. THE FAULT THAT IS NOT THE FETCH: the fetch succeeds and the CHECKOUT fails,
 * because a narrow remote.origin.fetch left no remote-tracking ref behind. This
 * is the shape #1629 reported — "checkout failed", with the fetch fine — and the
 * two must not be reported with the same four words. */
{
  const w = world({ branches: ['steward/live'], singleBranch: true });
  const r = runLap(w.work, [[2002, 'steward/live']]);
  check('a fetch that works and a checkout that does not still ends the lap cleanly',
        r.code === 0, `exit ${r.code}`);
  check('…and is reported as the CHECKOUT, naming both refs',
        /CHECKOUT of `origin\/steward\/live` into `lap\/2002` FAILED/.test(r.out));
  check('…and never blames the fetch, which succeeded',
        !/FETCH of `steward\/live` FAILED/.test(r.out));
  check("…and carries git's own message",
        /is not a commit/i.test(r.out));
  check('…and names the remote-tracking ref as the thing that is missing',
        /remote-TRACKING ref is what is missing/.test(r.out));
  rmSync(w.box, { recursive: true, force: true });
}

/* 3. THE CAUSE WHERE THE NAMED PR IS INNOCENT: a working tree the lap arrived
 * with dirty. checkout refuses to overwrite local changes, so the guard fires on
 * whichever PR happens to be next — and naming that PR without naming the dirt
 * sends the reader to the wrong branch entirely. */
{
  const w = world({ branches: ['steward/dirty'] });
  writeFileSync(path.join(w.work, 'f.txt'), 'uncommitted work from the last iteration\n');
  const r = runLap(w.work, [[2003, 'steward/dirty']]);
  check('a dirty tree does not crash the lap', r.code === 0, `exit ${r.code}`);
  check('…and is reported as the CHECKOUT', /CHECKOUT of .* FAILED/.test(r.out));
  check("…and carries git's own refusal",
        /local changes to the following files would be overwritten/i.test(r.out));
  check('…and says the tree was not clean when the lap got here',
        /working tree was NOT clean/.test(r.out));
  check('…and names the dirty path', /^\s+M f\.txt$/m.test(r.out));
  rmSync(w.box, { recursive: true, force: true });
}

/* 4. THE HAPPY PATH IS UNCHANGED — the evidence must not cost the lap its job. */
{
  const w = world({ branches: [] });
  git(w.work, 'push', '-q', 'origin', 'HEAD:refs/heads/steward/current');
  git(w.work, 'fetch', '-q', 'origin');
  const r = runLap(w.work, [[2004, 'steward/current']]);
  check('a branch that is level with dev laps normally', r.code === 0, `exit ${r.code}`);
  check('…and gets past both guards', !/FAILED — left alone/.test(r.out));
  check('…and is reported as already current',
        /already current — nothing to lap/.test(r.out) && /already-current=1/.test(r.out));
  rmSync(w.box, { recursive: true, force: true });
}

/* 5. DRIFT GUARD. The whole fault was `2>/dev/null` on these two lines: the
 * message existed and was thrown away. Reinstating it would pass every case
 * above that looks at the branch name and fail only the ones that look for git's
 * words, so it is asserted directly on the source too. */
{
  const src = readFileSync(LAP, 'utf8')
    .split('\n').filter((l) => !l.trim().startsWith('#')).join('\n');
  const silenced = /git (fetch|checkout)[^\n]*2>\/dev\/null[^\n]*(fetch|checkout) failed/.exec(src);
  check("neither guard discards git's stderr any more",
        silenced === null, silenced ? silenced[0] : 'both log to a file and tail it');
  check('and neither of the four-word labels survives',
        !/say "  (fetch|checkout) failed"/.test(src));
}

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);
