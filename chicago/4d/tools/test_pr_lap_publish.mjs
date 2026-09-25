#!/usr/bin/env node
/**
 * test_pr_lap_publish.mjs — the lap publishes the mirror BEFORE it rebuilds the
 * derived layer, so a rebuild that reaches manifest step 156 can finish.
 *
 * WHY THIS EXISTS (T-1521). `site/4d/` is generated and untracked (T-0938), so the
 * lap's checkout has no mirror at all — and step 156 of 156,
 * `tools/rebuild_closing_set.py --build`, READS it. Rather than write a number it
 * did not take, it refuses:
 *
 *     REFUSED to write docs/RESEARCH/closing-convergence-2026-09.md: the mirror
 *     is not published, so the published-resident count was not taken.
 *
 * `rederive.mjs --run` therefore failed, and the lap left the PR alone — on EVERY
 * lap, for ever, because the next lap reaches the same step and cannot finish
 * either. MEASURED 2026-09-21, lap run 35624254338 on PR #1630:
 *
 *     the derived-layer rebuild failed — left alone:
 *         [156/156] python3 tools/rebuild_closing_set.py --build
 *     PR lap: pushed=0 already-current=0 left-alone=2
 *
 * From outside that is indistinguishable from a queue the lap has not reached, and
 * three PRs with GREEN gates (#1629, #1630, #1631) sat unmergeable while the lap
 * reported success.
 *
 * WHAT IS REAL HERE AND WHAT IS FAKED. The lap is the REAL
 * `.github/steward/pr-lap.sh` and git is the REAL git, run against a REAL bare
 * remote with a base branch, a PR branch, and the base moved ahead — so the merge,
 * the commit and the push are the genuine article. `gh` is faked to answer the
 * PR list (the only call this path makes), and `chicago/4d/tools/` holds STUBS:
 * the point is the ORDER of publish and rebuild, and the real tools want the whole
 * dataset and ~20 seconds. The rederive stub models step 156 exactly — it refuses,
 * with that refusal's own words, unless the published residents are there to count.
 *
 * Case 2 runs the SAME suite against a copy of the lap with the publish neutered,
 * and requires it to FAIL. A regression test that cannot see the regression is
 * decoration; this one is shown to catch it.
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
  if (r.status !== 0) throw new Error(`git ${args.join(' ')}\n${r.stdout}${r.stderr}`);
  return r.stdout;
};

/**
 * Build a repository the lap can really lap, run the (possibly patched) lap over
 * it, and hand back what it said plus whether the branch actually moved.
 */
function runLap({ lapSource = null } = {}) {
  const box = mkdtempSync(path.join(tmpdir(), 'prlappub-'));
  const bare = path.join(box, 'remote.git');
  const work = path.join(box, 'work');
  const bin = path.join(box, 'bin');
  mkdirSync(bin, { recursive: true });

  git(box, 'init', '--quiet', '--bare', '-b', 'dev', bare);
  git(box, 'clone', '--quiet', bare, work);
  git(work, 'config', 'user.name', 'fixture');
  git(work, 'config', 'user.email', 'fixture@example.com');

  // The stub tool tree. `site/4d/` is ignored here exactly as it is in the repo,
  // so a published mirror can never reach a commit — which is the whole reason
  // the lap's checkout has none to begin with.
  const tools = path.join(work, 'chicago', '4d', 'tools');
  mkdirSync(tools, { recursive: true });
  writeFileSync(path.join(work, '.gitignore'), 'site/4d/\n');
  // Present but routing nothing: the lap reads the base's .gitattributes for
  // driver names, and an absent one is a `git show` failure in the middle of a
  // passing run — noise this suite should not be teaching anyone to ignore.
  writeFileSync(path.join(work, '.gitattributes'), '# no merge drivers in the fixture\n');
  writeFileSync(path.join(work, 'chicago', '4d', 'data.json'), '{"town": 1}\n');

  // STEP 156, in miniature and in its own words: the published-resident count is
  // taken from the mirror, and a mirror that is not there is not a count of zero.
  writeFileSync(path.join(tools, 'rederive.mjs'), `#!/usr/bin/env node
import { existsSync, writeFileSync } from 'node:fs';
if (!existsSync('../../site/4d/data/residents')) {
  console.log('[156/156] python3 tools/rebuild_closing_set.py --build');
  console.log('FAILED: python3 tools/rebuild_closing_set.py --build');
  console.log('  REFUSED to write docs/RESEARCH/closing-convergence-2026-09.md: the');
  console.log('  mirror is not published, so the published-resident count was not taken.');
  process.exit(1);
}
writeFileSync('derived.json', JSON.stringify({ rebuilt: Date.now() }) + '\\n');
console.log('[156/156] ok');
`);
  // publish.sh runs with chicago/4d as its cwd, and writes the mirror at the
  // repository root — the same two-levels-up relation the real one has.
  writeFileSync(path.join(tools, 'publish.sh'), `#!/usr/bin/env bash
set -euo pipefail
mkdir -p ../../site/4d/data/residents
echo '{}' > ../../site/4d/data/residents/index.json
echo published
`);
  writeFileSync(path.join(tools, 'ticket.mjs'), 'process.exit(0);\n');
  writeFileSync(path.join(tools, 'stamp-changelog.mjs'), 'process.exit(0);\n');
  writeFileSync(path.join(tools, 'compile_scene.py'), 'pass\n');
  writeFileSync(path.join(tools, 'tickets.sh'), '#!/usr/bin/env bash\nexit 0\n');
  for (const f of ['publish.sh', 'tickets.sh']) chmodSync(path.join(tools, f), 0o755);

  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'fixture: the tool tree');
  git(work, 'push', '--quiet', 'origin', 'dev');

  // The PR branch, and then the base moving ahead of it — which is the only
  // condition under which the lap does anything at all.
  git(work, 'checkout', '--quiet', '-b', 'steward/t-9999');
  writeFileSync(path.join(work, 'chicago', '4d', 'branch.md'), 'the branch its own work\n');
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'the PR');
  git(work, 'push', '--quiet', 'origin', 'steward/t-9999');
  const branchHead = git(work, 'rev-parse', 'HEAD').trim();

  git(work, 'checkout', '--quiet', 'dev');
  writeFileSync(path.join(work, 'chicago', '4d', 'data.json'), '{"town": 2}\n');
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'dev moved');
  git(work, 'push', '--quiet', 'origin', 'dev');

  // The list is the only thing the lap asks gh for on this path.
  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
if [ "$1" = "api" ]; then printf '%b' '7\\tsteward/t-9999\\n'; fi
exit 0
`);
  chmodSync(path.join(bin, 'gh'), 0o755);

  let lap = LAP;
  if (lapSource !== null) {
    lap = path.join(box, 'pr-lap.sh');
    writeFileSync(lap, lapSource);
  }

  const r = spawnSync('bash', [lap], {
    cwd: work,
    encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`,
           GH_TOKEN: 'fake', LAP_BASE: 'dev', LAP_ONLY: '',
           GITHUB_REPOSITORY: 'kevinrhaas/chicago' },
  });
  const after = git(box, '--git-dir', bare, 'rev-parse', 'refs/heads/steward/t-9999').trim();
  rmSync(box, { recursive: true, force: true });
  const out = `${r.stdout || ''}${r.stderr || ''}`;
  const summary = (out.match(/^PR lap: .*$/m) || ['no summary line'])[0];
  return { code: r.status, out, summary, moved: after !== branchHead };
}

console.log('pr-lap.sh — the mirror is published before the derived layer is rebuilt');

/* 1. THE FIX. A rebuild that reads the mirror finishes, and the PR is pushed. */
{
  const r = runLap();
  check('a lap whose rebuild reaches step 156 pushes', /pushed=1/.test(r.out), r.summary);
  check('…and the PR branch really moved on the remote', r.moved);
  check('…and it is not left alone', /left-alone=0/.test(r.out));
  check('…and step 156 never had to refuse',
        !/the published-resident count was not taken/.test(r.out));
  check('…and the lap says it published before it rebuilt',
        /publishing the mirror, then rebuilding the derived layer/.test(r.out));
  check('the lap exits clean', r.code === 0, `exit ${r.code}`);
}

/* 2. THE SAME SUITE CATCHES THE FAULT. The publish is neutered — which is the lap
 *    as it stood on 2026-09-21 — and every assertion above must invert. */
{
  const raw = readFileSync(LAP, 'utf8');
  const PUBLISH = '( cd chicago/4d && bash tools/publish.sh ) >/tmp/lap-publish.log 2>&1';
  check('the publish lives in one place, so neutering it is a fair simulation',
        raw.split(PUBLISH).length === 2, `${raw.split(PUBLISH).length - 1} occurrence(s)`);
  const r = runLap({ lapSource: raw.replace(PUBLISH, 'true') });
  check('without the publish the PR is left alone', /left-alone=1/.test(r.out), r.summary);
  check('…and the branch does not move', !r.moved);
  check('…and the reason is step 156 refusing to count a mirror that is not there',
        /the published-resident count was not taken/.test(r.out));
  check('…and the lap still SAYS which step and why — the half that was working',
        /rebuild failed — left alone/.test(r.out));
}

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);
