#!/usr/bin/env node
/**
 * test_pr_lap_list.mjs — a lap that could not ASK never reports that it FOUND
 * nothing.
 *
 * WHY THIS EXISTS. On 2026-09-14 the PR lap was dispatched with LAP_ONLY=1257 to
 * lap a pull request sitting 39 commits behind `dev`. The run went GREEN:
 *
 *     GraphQL: API rate limit already exceeded for user ID 4193586.
 *     PR lap: pushed=0 already-current=0 left-alone=0 red=0
 *
 * `PRS=$(gh pr list …)` carries gh's exit status, and pr-lap.sh runs
 * `set -uo pipefail` WITHOUT `-e` — so the failure did not stop it. PRS was
 * empty, the loop ran zero times, and the summary it printed is character for
 * character what a healthy lap with nothing to do prints. Every lap inside that
 * rate-limit window reported clean while sweeping nothing, which is what a stuck
 * PR queue looks like from outside when the workflow list looks healthy.
 *
 * The same shape as the steward janitor's `set -e` abort (polecat-platform #165).
 * The janitor at least went red; this went green, which is worse.
 *
 * THE SCRIPT IS NOT COPIED HERE. Each case runs the REAL `.github/steward/
 * pr-lap.sh` with `gh` and `git` faked on PATH, so an edit that reintroduces the
 * fault fails here rather than on a Saturday morning's PR queue. The fakes stop
 * the run immediately after the list is taken — everything this suite is about
 * has happened by then, and the lap's real body wants a repository.
 */
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync, rmSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const LAP = path.resolve(path.dirname(new URL(import.meta.url).pathname),
                         '..', '..', '..', '.github', 'steward', 'pr-lap.sh');

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

/** Run the real lap with a fake `gh` that behaves as asked. */
function runLap({ ghExit = 0, ghOut = '', only = '' }) {
  const box = mkdtempSync(path.join(tmpdir(), 'prlap-'));
  const bin = path.join(box, 'bin');
  mkdirSync(bin, { recursive: true });

  // The PR-list call is what is under test; everything else gh is asked for
  // later is irrelevant, because the lap does not reach it in these cases.
  // `gh api`, not `gh pr list`: the list moved to REST because `gh pr list` is a
  // GraphQL call and the steward PAT's GraphQL budget is what ran out on
  // 2026-09-14 while REST answered normally. Matching on `api` here means a
  // silent revert to the GraphQL form fails this suite rather than the fleet.
  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
if [ "$1" = "api" ]; then
  # %b, NOT %s: the list is TAB-separated and newline-delimited, and %s would
  # emit the escapes literally. awk -F'\\t' would then find no tab, put the whole
  # line in $1, and every --only match would fail — making this suite pass case 3
  # for the wrong reason and fail case 4 for no reason at all.
  printf '%b' ${JSON.stringify(ghOut)}
  exit ${ghExit}
fi
exit 0
`);
  // The lap registers merge drivers and reads .gitattributes before the list.
  // A fake git that answers those checks and nothing else keeps the suite about
  // the list rather than about git.
  writeFileSync(path.join(bin, 'git'), `#!/usr/bin/env bash
case "$*" in
  *"rev-parse --show-toplevel"*) echo "${box}" ;;
  *"--get merge."*)              echo "some-driver" ;;   # every driver registered
  *"config"*|*"fetch"*|*"remote"*) : ;;
  *) : ;;
esac
exit 0
`);
  for (const f of ['gh', 'git']) chmodSync(path.join(bin, f), 0o755);

  // .gitattributes is read for the driver names; empty means nothing to verify.
  mkdirSync(path.join(box, '.git', 'info'), { recursive: true });
  writeFileSync(path.join(box, '.gitattributes'), '');

  const r = spawnSync('bash', [LAP], {
    cwd: box,
    encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`,
           GH_TOKEN: 'fake', LAP_ONLY: only, GITHUB_REPOSITORY: 'kevinrhaas/custom' },
  });
  rmSync(box, { recursive: true, force: true });
  return { code: r.status, out: `${r.stdout || ''}${r.stderr || ''}` };
}

console.log('pr-lap.sh — a lap that could not ask never reports that it found nothing');

/* 1. THE FAULT. gh fails; the lap must NOT exit 0 having swept nothing. */
{
  const r = runLap({ ghExit: 1, ghOut: '' });
  check('a failed PR-list call fails the lap', r.code !== 0, `exit ${r.code}`);
  check('…and says the lap could not see its PRs',
        /cannot see the pull requests/i.test(r.out));
  check('…and never claims it found nothing to do',
        !/PR lap: pushed=0 already-current=0 left-alone=0 red=0/.test(r.out));
}

/* 2. The honest empty queue still passes — the guard must not cost that. */
{
  const r = runLap({ ghExit: 0, ghOut: '' });
  check('a genuinely empty queue is not an error', r.code === 0, `exit ${r.code}`);
  check('…and still prints the summary', /PR lap: pushed=0/.test(r.out));
}

/* 3. A dispatch naming a PR that is not lappable is loud, not silent. */
{
  const r = runLap({ ghExit: 0, ghOut: '1290\tsteward/other\n', only: '1257' });
  check('LAP_ONLY that matches nothing fails the lap', r.code !== 0, `exit ${r.code}`);
  check('…and names the number it could not find', /LAP_ONLY=1257/.test(r.out));
  check('…and says `hold` is filtered before this point — the case that cost an hour',
        /hold/.test(r.out));
}

/* 4. …and a dispatch that DOES match is unaffected. */
{
  const r = runLap({ ghExit: 0, ghOut: '1257\tsteward/t-0464\n1290\tsteward/other\n', only: '1257' });
  check('LAP_ONLY that matches proceeds past the guard',
        !/LAP_ONLY=1257 matched no/.test(r.out));
}

/* 5. NO GRAPHQL-BACKED `gh` CALL SURVIVES IN THE LAP.
 *
 * A drift guard rather than a behaviour test, and it earns its place: the list
 * was moved to REST because `gh pr list` is GraphQL and the steward PAT's
 * GraphQL budget is the one that runs out — and lap 307 then refused five PRs
 * correctly and told none of them why, because `gh pr view` and `gh pr comment`
 * are GraphQL too. The budget is shared with the loop, the janitor and Manager,
 * so one reintroduced `gh pr …` blinds the lap again on a busy afternoon.
 * gh-rest.sh:18-30 lists which verbs go through GraphQL. */
{
  const src = readFileSync(LAP, 'utf8')
    .split('\n').filter((l) => !l.trim().startsWith('#')).join('\n');
  const graphql = /\bgh (pr|issue) (comment|create|merge|view|list|edit|close)\b/.exec(src);
  check('no GraphQL-backed `gh pr|issue` call is left in the lap',
        graphql === null, graphql ? graphql[0] : 'every gh call is `gh api`');
}

/* 6. THE LAP DOES NOT GATE — it pushes and lets CI do it.
 *
 * A drift guard for the root-cause fix. The lap used to run the whole of
 * `check.sh` before pushing, which is redundant — chicago-4d-check.yml fires on
 * `push` to any branch under chicago/4d/** AND on `pull_request` — and it was
 * why the queue never converged: ~15 minutes per PR, against merges landing
 * every few minutes, each of which re-dirties every open PR (T-0857).
 *
 * Measured 2026-09-14: lap 297 42.1 min, lap 307 19.2 min for ONE push, while
 * laps that pushed nothing took 1.4 min. #1315 and #1319 were each resolved,
 * gated green, pushed, and `dirty` again before they could merge.
 *
 * Reinstating that gate would re-break it silently, so it is asserted here. */
{
  const src = readFileSync(LAP, 'utf8')
    .split('\n').filter((l) => !l.trim().startsWith('#')).join('\n');
  const gates = /\.\/tools\/check\.sh|tools\/check\.sh/.exec(src);
  check('the lap does not run check.sh itself — CI gates the push',
        gates === null, gates ? `found ${gates[0]}` : 'CI is the gate');
}

/* 7. THE DERIVED LAYER IS REBUILT ON EVERY MERGE, NOT ONLY ON A CONFLICT.
 *
 * The case that is easy to lose, because it has no conflict to look at: `dev`
 * changes an INPUT to a derived file that the branch never touched. git reports
 * nothing — there is no disagreement, only a new fact — so a rebuild keyed to
 * conflicts never fires, and the branch carries a file that no longer follows
 * from its own inputs.
 *
 * CAUGHT LIVE on #1316, 2026-09-14: lap 314 merged `dev` in with ZERO conflicts
 * and pushed; the gate went red on one step of 397, `…and the later HOME
 * addresses re-derive through the residence clauses`. `dev` had just taken
 * #1315, which added a fourth Sherman to the residents layer, and
 * residence_back_projection.json said 57 adjudicated where its tool derives 58.
 *
 * These are source assertions rather than a behaviour run: the fakes stop the
 * lap at the list, and reaching the rebuild wants a real repository and 19
 * seconds of tools. What they pin is the SHAPE that was wrong — a rebuild
 * reachable only from inside the conflict branch, and a per-PR flag that is not
 * cleared per PR. */
{
  const raw = readFileSync(LAP, 'utf8');
  const src = raw.split('\n').filter((l) => !l.trim().startsWith('#')).join('\n');

  const runs = src.match(/rederive\.mjs --run/g) || [];
  check('the lap still rebuilds the derived layer somewhere',
        runs.length >= 1, `${runs.length} call site(s)`);

  // The unconditional site is the one this case is about: guarded by the
  // already-done flag rather than by `$REAL`, so a clean merge reaches it too.
  check('…on a path a CLEAN merge reaches, not only inside the conflict branch',
        /if \[ -z "\$\{REDERIVED:-\}" \][\s\S]{0,200}?rederive\.mjs --run/.test(src),
        'guarded by REDERIVED, not by $REAL');

  // A flag set mid-body outlives the iteration unless it is reset at the top —
  // and a stale one would skip the rebuild for the NEXT PR, silently.
  const loop = src.indexOf("while IFS=$'\\t' read -r N BR; do");
  const reset = src.indexOf('REDERIVED=', loop);
  const set = src.indexOf('REDERIVED=1', loop);
  check('…and the per-PR flag is cleared at the top of the loop, before it is set',
        loop !== -1 && reset !== -1 && reset < set,
        loop === -1 ? 'loop head not found' : `reset@${reset} set@${set}`);
}

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);
