#!/usr/bin/env node
/**
 * test_pr_lap_current.mjs — a branch already current with the base, whose gate is
 * RED, is re-derived by the lap rather than reported as having nothing to lap.
 *
 * WHY THIS EXISTS (T-1362). The lap rebuilt the derived layer only INSIDE a merge,
 * and a branch level with `dev` has nothing to merge, so it never got there. #1480
 * landed a new gate on dev; #1487 already agreed with dev about every file; the lap
 * printed `already current — nothing to lap` while four manifest-owned files sat
 * stale on it and its gate read 4 red of 513. `rederive.mjs --run` turned all four
 * green. Nobody ran it. #1518 sat the same way for nearly two hours.
 *
 * WHAT IS REAL HERE AND WHAT IS FAKED. The lap is the REAL `.github/steward/
 * pr-lap.sh` and git is the REAL git, over a REAL bare remote with a PR branch
 * already level with `dev`. `gh` is faked: it answers the PR list, the head's
 * check runs (the gate's verdict is what each case varies) and the PR's comments,
 * and records any comment the lap posts. `chicago/4d/tools/` holds STUBS: the
 * rederive stub derives `derived.json` from `data.json` exactly, so a branch whose
 * derived file does not follow from its inputs is stale in the same sense the
 * manifest's files are, and it logs every run so a case can assert the rebuild was
 * NOT spent.
 *
 * The last case runs the suite against the lap with its old one-line exit restored
 * and requires the fix's assertion to fail: a regression test that cannot see the
 * regression is decoration.
 */
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync, rmSync, readFileSync, existsSync } from 'node:fs';
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
  if (r.status !== 0) throw new Error(`git ${args.join(' ')}\n${r.stdout}${r.stderr}`);
  return r.stdout;
};

/**
 * A branch level with `dev`, its derived file stale or not, its gate reading
 * `verdict`, and the PR carrying `priorComment` (with `{sha}` filled in) if given.
 */
function runLap({ stale, verdict, priorComment = '', lapSource = null }) {
  const box = mkdtempSync(path.join(tmpdir(), 'prlapcur-'));
  const bare = path.join(box, 'remote.git');
  const work = path.join(box, 'work');
  const bin = path.join(box, 'bin');
  const ranLog = path.join(box, 'rederive-ran.log');
  const posted = path.join(box, 'posted.json');
  mkdirSync(bin, { recursive: true });

  git(box, 'init', '--quiet', '--bare', '-b', 'dev', bare);
  git(box, 'clone', '--quiet', bare, work);
  git(work, 'config', 'user.name', 'fixture');
  git(work, 'config', 'user.email', 'fixture@example.com');

  const app = path.join(work, 'chicago', '4d');
  const tools = path.join(app, 'tools');
  mkdirSync(tools, { recursive: true });
  writeFileSync(path.join(work, '.gitignore'), 'site/4d/\n');
  writeFileSync(path.join(work, '.gitattributes'), '# no merge drivers in the fixture\n');
  writeFileSync(path.join(app, 'data.json'), '{"town": 1}\n');
  writeFileSync(path.join(app, 'derived.json'), '{"from": 1}\n');

  // A derivation in miniature: the output is a pure function of the input, so
  // re-running it on a fresh tree writes the identical bytes and git sees nothing.
  writeFileSync(path.join(tools, 'rederive.mjs'), `#!/usr/bin/env node
import { readFileSync, writeFileSync, appendFileSync } from 'node:fs';
appendFileSync(${JSON.stringify(ranLog)}, process.argv.slice(2).join(' ') + '\\n');
const town = JSON.parse(readFileSync('data.json', 'utf8')).town;
writeFileSync('derived.json', JSON.stringify({ from: town }).replace(':', ': ') + '\\n');
console.log('[1/1] ok');
`);
  writeFileSync(path.join(tools, 'publish.sh'), '#!/usr/bin/env bash\nmkdir -p ../../site/4d\necho published\n');
  writeFileSync(path.join(tools, 'ticket.mjs'), 'process.exit(0);\n');
  writeFileSync(path.join(tools, 'stamp-changelog.mjs'), 'process.exit(0);\n');
  writeFileSync(path.join(tools, 'compile_scene.py'), 'pass\n');
  writeFileSync(path.join(tools, 'tickets.sh'), '#!/usr/bin/env bash\nexit 0\n');
  for (const f of ['publish.sh', 'tickets.sh']) chmodSync(path.join(tools, f), 0o755);

  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'fixture: the tool tree');
  git(work, 'push', '--quiet', 'origin', 'dev');

  // The PR branch: it moves an input. Stale means it did not re-derive after.
  git(work, 'checkout', '--quiet', '-b', 'steward/t-9999');
  writeFileSync(path.join(app, 'data.json'), '{"town": 2}\n');
  if (!stale) writeFileSync(path.join(app, 'derived.json'), '{"from": 2}\n');
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'the PR');
  git(work, 'push', '--quiet', 'origin', 'steward/t-9999');
  const branchHead = git(work, 'rev-parse', 'HEAD').trim();
  // ...and `dev` does NOT move: the branch is level with it, which is the case.
  git(work, 'checkout', '--quiet', 'dev');

  const comment = priorComment.replaceAll('{sha}', branchHead.slice(0, 12));
  const runs = verdict
    ? { check_runs: [{ name: 'gate', status: verdict.split(':')[0],
                       conclusion: verdict.split(':')[1] === 'none' ? null : verdict.split(':')[1],
                       started_at: '2026-10-04T10:00:00Z' }] }
    : { check_runs: [] };
  // gh's own --jq is applied by piping the canned JSON through the real jq, so the
  // lap's filter is exercised as written rather than bypassed. The JSON is served
  // from FILES: a comment body carries backticks, and inlined into the script's
  // double quotes bash would run them as command substitutions.
  const runsFile = path.join(box, 'check-runs.json');
  const commentsFile = path.join(box, 'comments.json');
  writeFileSync(runsFile, JSON.stringify(runs));
  writeFileSync(commentsFile, JSON.stringify(comment ? [{ body: comment }] : []));
  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
args="$*"; jqf=""
prev=""; for a in "$@"; do [ "$prev" = "--jq" ] && jqf="$a"; prev="$a"; done
case "$args" in
  *"-X POST"*comments*) cat > ${JSON.stringify(posted)}; exit 0 ;;
  *check-runs*) jq -r "$jqf" ${JSON.stringify(runsFile)}; exit 0 ;;
  *comments*) jq -r "$jqf" ${JSON.stringify(commentsFile)}; exit 0 ;;
  *pulls*) printf '%b' '7\\tsteward/t-9999\\n'; exit 0 ;;
esac
exit 0
`);
  chmodSync(path.join(bin, 'gh'), 0o755);

  let lap = LAP;
  if (lapSource !== null) {
    lap = path.join(box, 'pr-lap.sh');
    writeFileSync(lap, lapSource);
  }
  const r = spawnSync('bash', [lap, '--repo', 'kevinrhaas/chicago'], {
    cwd: work,
    encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`,
           GH_TOKEN: 'fake', LAP_BASE: 'dev', LAP_ONLY: '' },
  });
  const after = git(box, '--git-dir', bare, 'rev-parse', 'refs/heads/steward/t-9999').trim();
  const derivedAfter = git(box, '--git-dir', bare, 'show', 'refs/heads/steward/t-9999:chicago/4d/derived.json');
  const ran = existsSync(ranLog) ? readFileSync(ranLog, 'utf8') : '';
  const post = existsSync(posted) ? JSON.parse(readFileSync(posted, 'utf8')).body : null;
  rmSync(box, { recursive: true, force: true });
  const out = `${r.stdout || ''}${r.stderr || ''}`;
  const summary = (out.match(/^PR lap: .*$/m) || ['no summary line'])[0];
  return { code: r.status, out, summary, moved: after !== branchHead, derivedAfter, ran, post,
           sha: branchHead.slice(0, 12) };
}

console.log('pr-lap.sh — a branch level with the base and red is re-derived, not skipped');

/* 1. THE FIX: current, red, and stale — #1487's shape. */
{
  const r = runLap({ stale: true, verdict: 'completed:failure' });
  check('a current branch whose gate is red is re-derived', /re-deriving in place/.test(r.out), r.summary);
  check('…and pushed', /pushed=1/.test(r.out));
  check('…and the PR branch really moved on the remote', r.moved);
  check('…and the derived file now follows from its inputs', r.derivedAfter === '{"from": 2}\n',
        JSON.stringify(r.derivedAfter));
  check('…and it no longer says "nothing to lap"', !/nothing to lap/.test(r.out));
  check('…and posts no comment, because it fixed what it found', r.post === null);
  check('the lap exits clean', r.code === 0, `exit ${r.code}`);
}

/* 2. RED FOR THE BRANCH'S OWN REASONS: the rebuild moves nothing, so nothing is
 *    pushed — no empty lap commit — and the PR is told, once, with the head named. */
{
  const r = runLap({ stale: false, verdict: 'completed:failure' });
  check('a red branch the rebuild cannot change is not pushed', !r.moved && /pushed=0/.test(r.out), r.summary);
  check('…and the lap says the red is not a stale derivation', /NOTHING CHANGED/.test(r.out));
  check('…and it is counted left alone, not already current', /left-alone=1/.test(r.out) && /already-current=0/.test(r.out));
  check('…and says so on the PR, naming the head it re-derived',
        r.post !== null && r.post.includes(`re-derived \`${r.sha}\` and nothing changed`),
        r.post ? r.post.split('\n')[0] : 'no comment');
}

/* 3. ...AND DOES NOT PAY FOR THE SAME NO-OP REBUILD ON THE NEXT LAP. */
{
  const r = runLap({ stale: false, verdict: 'completed:failure',
                     priorComment: 'PR lap: re-derived `{sha}` and nothing changed, so the lap left this red branch alone.' });
  check('a head the lap already re-derived to no effect is not rebuilt again', r.ran === '', JSON.stringify(r.ran));
  check('…and no second comment is posted', r.post === null);
  check('…and the lap says why it left it', /already moved nothing/.test(r.out), r.summary);
}

/* 4. THE CLEAN PATH COSTS ONE QUESTION AND NO REBUILD — even on a stale tree,
 *    because a green or still-running gate is not the lap's to second-guess. */
for (const verdict of ['completed:success', 'in_progress:none', '']) {
  const r = runLap({ stale: true, verdict });
  const label = verdict || 'no gate on the head';
  check(`gate ${label}: reported already current`,
        /already current — nothing to lap/.test(r.out) && /already-current=1/.test(r.out), r.summary);
  check(`gate ${label}: …and the rebuild is never run`, r.ran === '', JSON.stringify(r.ran));
  check(`gate ${label}: …and the branch does not move`, !r.moved);
}

/* 5. THE SAME SUITE CATCHES THE FAULT: the lap's old one-line exit restored. */
{
  const raw = readFileSync(LAP, 'utf8');
  const GUARD = 'if [ "$(git rev-list --count "HEAD..origin/$BASE")" -eq 0 ]; then\n';
  check('the already-current guard lives in one place, so restoring it is a fair simulation',
        raw.split(GUARD).length === 2, `${raw.split(GUARD).length - 1} occurrence(s)`);
  const old = raw.replace(GUARD,
    `${GUARD}    say "  already current — nothing to lap"; NOOP=$((NOOP+1)); continue\n`);
  const r = runLap({ stale: true, verdict: 'completed:failure', lapSource: old });
  check('with the old exit, the red current branch is skipped', /already-current=1/.test(r.out), r.summary);
  check('…and stays stale on the remote', !r.moved && r.derivedAfter === '{"from": 1}\n');
}

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);
