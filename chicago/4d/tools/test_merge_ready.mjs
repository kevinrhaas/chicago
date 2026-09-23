#!/usr/bin/env node
/**
 * test_merge_ready.mjs — the thing that merges a finished pull request, tested
 * in the states that actually kept this repository's queue from draining.
 *
 * WHY THIS EXISTS. On 2026-09-14 the PR lap was fixed twice — it could not SEE
 * its pull requests (GraphQL budget), then it gated for ~7 minutes per PR
 * against merges landing every few minutes — and after both fixes the queue
 * still did not drain, because NOTHING MERGED A FINISHED PULL REQUEST. Three
 * pieces each assumed one of the others did it:
 *
 *   pr-lap.sh header       "auto-merge does that once `gate` goes green"
 *   steward-janitor.yml    "`custom` merges through the lap plus auto-merge"
 *                          — while deliberately excluding `custom` from itself
 *   chicago-4d-bake.yml    the ONLY `gh pr merge --auto` in the repo, on bakes
 *
 * Measured the same day: #1327 and #1312 both merged with `auto_merge: off`.
 * Auto-merge was armed by hand or not at all.
 *
 * THE SCRIPT IS NOT COPIED HERE. Each case runs the REAL
 * `.github/steward/merge-ready.sh` with `gh` faked on PATH, so a change that
 * makes it merge something it should not fails here rather than on `dev`.
 */
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync, rmSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const SH = path.resolve(path.dirname(new URL(import.meta.url).pathname),
                        '..', '..', '..', '.github', 'steward', 'merge-ready.sh');

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

/**
 * Run the real script against a fake `gh`.
 *  list      newline-separated PR numbers the list call answers with
 *  listExit  its exit status
 *  states    { "<n>": "clean" | "blocked" | ... } answered for each PR
 *  only      MERGE_ONLY
 *  dry       MERGE_DRY_RUN
 * Every `gh api -X PUT .../merge` is appended to a file the caller reads back,
 * because "did it merge?" is the only question that matters here.
 */
function run({ list = '', listExit = 0, states = {}, only = '', dry = '' }) {
  const box = mkdtempSync(path.join(tmpdir(), 'mergeready-'));
  const bin = path.join(box, 'bin');
  mkdirSync(bin, { recursive: true });
  const merges = path.join(box, 'merges.txt');

  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
# the merge itself — recorded, never performed
for a in "$@"; do
  case "$a" in */merge) echo "$*" >> ${JSON.stringify(merges)}; exit 0 ;; esac
done
# the PR list
case "$*" in
  *"pulls?state=open"*)
    printf '%b' ${JSON.stringify(list)}
    exit ${listExit} ;;
esac
# a single PR's fields: which one is asked for is in the path
N=""
for a in "$@"; do
  case "$a" in
    repos/*/pulls/*) N="\${a##*/}" ;;
  esac
done
case "$*" in
  *".mergeable_state"*) echo "$(node -e '
      const s=JSON.parse(process.argv[1]); process.stdout.write(s[process.argv[2]]||"unknown");
    ' ${JSON.stringify(JSON.stringify(states))} "$N")" ;;
  *".head.sha"*)        echo "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef" ;;
  *".title"*)           echo "a pull request" ;;
esac
exit 0
`);
  chmodSync(path.join(bin, 'gh'), 0o755);

  const r = spawnSync('bash', [SH], {
    cwd: box,
    encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`,
           GH_TOKEN: 'fake', MERGE_ONLY: only, MERGE_DRY_RUN: dry,
           GITHUB_REPOSITORY: 'kevinrhaas/custom' },
  });
  let did = '';
  try { did = readFileSync(merges, 'utf8'); } catch { did = ''; }
  rmSync(box, { recursive: true, force: true });
  return { code: r.status, out: `${r.stdout || ''}${r.stderr || ''}`, merges: did };
}

console.log('merge-ready.sh — merges what GitHub calls clean, and nothing else');

/* 1. THE WHOLE POINT. A clean PR is merged. */
{
  const r = run({ list: '1319\n', states: { 1319: 'clean' } });
  check('a `clean` PR is merged', /pulls\/1319\/merge/.test(r.merges), r.merges.trim() || 'nothing merged');
  check('…by squash, as every other merge in this repo is',
        /merge_method=squash/.test(r.merges));
  check('…with the head sha pinned, so a push mid-read loses the race',
        /sha=deadbeef/.test(r.merges));
  check('…and the run says so', /#1319 {2}MERGED/.test(r.out));
}

/* 2. THE STATE THAT MATTERS MOST: a PR mid-gate must NOT be merged. `blocked`
 *    is what every PR reads while its gate runs, which after a lap is all of
 *    them at once. Merging on `blocked` would ship ungated trees to `dev`. */
{
  const r = run({ list: '1315\n', states: { 1315: 'blocked' } });
  check('a `blocked` PR is NOT merged — its gate has not passed',
        r.merges === '', r.merges.trim());
  check('…and is reported as waiting rather than skipped in silence',
        /not green yet/.test(r.out));
}

/* 3. `dirty` is the lap's job, and merging it is not possible anyway. */
{
  const r = run({ list: '1268\n', states: { 1268: 'dirty' } });
  check('a `dirty` PR is left for the lap', r.merges === '', r.merges.trim());
  check('…and says which tool owns it', /lap's job/.test(r.out));
}

/* 4. A MIXED QUEUE — the real shape after a lap: some green, most still gating.
 *    Exactly one merge, and it is the right one. */
{
  const r = run({ list: '1319\n1315\n1316\n1242\n',
                  states: { 1319: 'clean', 1315: 'blocked', 1316: 'blocked', 1242: 'dirty' } });
  const n = (r.merges.match(/\/merge/g) || []).length;
  check('one clean PR among four is merged, and only it', n === 1, `${n} merge call(s)`);
  check('…and it is 1319', /pulls\/1319\/merge/.test(r.merges));
  check('…and the summary counts the rest honestly',
        /merged=1 waiting-on-checks=2 needs-a-lap=1/.test(r.out),
        (r.out.match(/^merge-ready: .*$/m) || ['no summary line'])[0]);
}

/* 5. `unknown` IS RETRIED, NOT BELIEVED. GitHub computes mergeability lazily and
 *    answers `unknown` straight after a push — which is exactly when this runs.
 *    Believing the first answer would skip every PR the lap had just touched. */
{
  const r = run({ list: '1319\n', states: {} });   // always `unknown`
  check('a PR still computing is not merged', r.merges === '', r.merges.trim());
  check('…and it was asked more than once before giving up',
        /unknown/.test(r.out));
}

/* 6. A FAILED LIST FAILS THE RUN. `PRS=$(gh api …)` carries gh's status and this
 *    script has no `set -e`, so a failure leaves PRS empty and the loop runs
 *    zero times — printing character for character what a healthy empty queue
 *    prints. That is the shape that made the blind lap look green all morning
 *    (see test_pr_lap_list.mjs); it is not repeated here. */
{
  const r = run({ list: '', listExit: 1 });
  check('a failed PR-list call fails the run', r.code !== 0, `exit ${r.code}`);
  check('…and never reports an empty queue it never saw',
        !/merged=0 waiting-on-checks=0/.test(r.out));
}

/* 7. The honest empty queue still passes — the guard above must not cost that. */
{
  const r = run({ list: '', listExit: 0 });
  check('a genuinely empty queue is not an error', r.code === 0, `exit ${r.code}`);
  check('…and still prints the summary', /merged=0/.test(r.out));
}

/* 8. DRY RUN MERGES NOTHING. The flag exists so the first live run could be
 *    watched before it was trusted; a dry run that merged would be worse than
 *    no flag at all. */
{
  const r = run({ list: '1319\n', states: { 1319: 'clean' }, dry: '1' });
  check('a dry run merges nothing', r.merges === '', r.merges.trim());
  check('…and says what it would have done', /WOULD MERGE/.test(r.out));
}

/* 9. MERGE_ONLY THAT MATCHES NOTHING IS LOUD. Drafts and `hold` are filtered out
 *    of the list before this point, so a dispatch naming one gets no answer at
 *    all — and a silent no-op reads as "considered and declined". */
{
  const r = run({ list: '1315\n', states: { 1315: 'clean' }, only: '1210' });
  check('MERGE_ONLY that matches nothing fails the run', r.code !== 0, `exit ${r.code}`);
  check('…and names the number', /MERGE_ONLY=1210/.test(r.out));
  check('…and says `hold` is filtered before this point', /hold/.test(r.out));
  check('…and merged nothing while failing', r.merges === '', r.merges.trim());
}

/* 10. THE FILTER IS IN THE LIST QUERY, AND IT HAS TO STAY THERE. `hold` is the
 *     owner's park mechanism; a park a robot can overrule is not a park. This is
 *     a drift guard on the one line that enforces it. */
{
  const src = readFileSync(SH, 'utf8')
    .split('\n').filter((l) => !l.trim().startsWith('#')).join('\n');
  check('drafts are filtered out of the candidate list',
        /select\(\.draft==false\)/.test(src));
  check('`hold` is filtered out of the candidate list',
        /index\("hold"\) \| not/.test(src));
  check('no GraphQL-backed `gh pr|issue` verb is used — the budget that fails',
        /\bgh (pr|issue) (comment|create|merge|view|list|edit|close)\b/.exec(src) === null);
  check('the only state it merges on is `clean`',
        /^\s*clean\)/m.test(src) && !/blocked\|.*\)\s*$/m.test(src.replace(/blocked\|unstable\|has_hooks\)/, '')));
}

/* 11. THE WORKFLOW'S TRIGGER MUST BE ONE THAT FIRES FROM A NON-DEFAULT BRANCH.
 *
 * `schedule` and `workflow_run` fire ONLY from the repository's DEFAULT branch.
 * This repo's default is `main`; this workflow lives on `dev` and reaches `main`
 * only through promote-to-prod. A `schedule` written here would never fire once
 * — not late, not rarely: never — and the failure is SILENT, which is the whole
 * reason it is asserted rather than trusted to a comment.
 *
 * Checked 2026-09-14 rather than assumed: `main` carries 8 workflows and
 * chicago-4d-pr-lap.yml is not among them, yet the lap runs many times a day,
 * because `push:` triggers DO fire from the pushed branch's own copy; and every
 * scheduled run of chicago-4d-bake.yml reports `head_branch: main`.
 *
 * The first draft of this workflow had `schedule` and `workflow_run` and would
 * have merged nothing, ever, while looking entirely reasonable in review. */
{
  const wf = path.resolve(path.dirname(new URL(import.meta.url).pathname),
                          '..', '..', '..', '.github', 'workflows',
                          'chicago-4d-merge-ready.yml');
  const y = readFileSync(wf, 'utf8')
    .split('\n').filter((l) => !/^\s*#/.test(l)).join('\n');

  check('the workflow triggers on a push to dev — a trigger that fires from dev',
        /^on:[\s\S]*?^\s{2}push:\s*$[\s\S]*?branches:\s*\[\s*dev\s*\]/m.test(y));
  check('…and carries no `schedule`, which would never fire from a non-default branch',
        !/^\s{2}schedule:/m.test(y));
  check('…nor `workflow_run`, which has the same default-branch restriction',
        !/^\s{2}workflow_run:/m.test(y));
  check('…and still offers a manual dispatch', /^\s{2}workflow_dispatch:/m.test(y));
}

/* 12. THE WATCH LOOP MUST SURVIVE A SETTLED QUEUE, which is the success case.
 *
 * GitHub runs a `run:` block as `bash --noprofile --norc -eo pipefail {0}`, so
 * `-e` is on before the script's first line and a `set -uo pipefail` inside does
 * NOT turn it off. The loop counts how many pull requests are still `blocked`
 * with `grep -c`, and `grep -c` exits 1 when it counts nothing — so the step
 * died exactly when nothing was left waiting.
 *
 * Runs 2 and 3 on 2026-09-14 did their whole job, printed
 * `merged=0 waiting-on-checks=0 needs-a-lap=3`, and THEN exited 1. Run 1 passed
 * only because something was still gating. A failure that fires on success and
 * hides on failure is the worst shape available, so it is asserted here.
 *
 * Third time this GitHub default has bitten in one day: polecat-platform #165
 * aborted a janitor sweep on it, and pr-lap.sh's `PRS=$(...)` is its mirror. */
{
  const wf = path.resolve(path.dirname(new URL(import.meta.url).pathname),
                          '..', '..', '..', '.github', 'workflows',
                          'chicago-4d-merge-ready.yml');
  const y = readFileSync(wf, 'utf8');
  const body = y.split('\n').filter((l) => !/^\s*#/.test(l)).join('\n');
  check('the watch loop disarms the -e GitHub turns on for it',
        /^\s*set \+e\s*$/m.test(body));
  check('…and the blocked-count never fails the step when it counts nothing',
        /grep -c '\^blocked\$' \|\| true/.test(body));
}

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);
