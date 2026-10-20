#!/usr/bin/env node
/**
 * test_pr_lap_package.mjs — the lap unpacks the Glessner package again after merging dev (T-2907).
 *
 * WHY THIS EXISTS. The three v4 Glessner GLBs too large to commit are a packed archive under
 * docs/RESEARCH/glessner-v4-recovery/, and publish.sh materializes them as IGNORED files. The
 * lap's clone laps every PR in turn and an ignored file survives every checkout and merge, so
 * once dev repacks the archive the copy on disk is the old one, and publish.sh refuses it:
 *
 *     Glessner v4 package: assets/gltf/glessner_house__as_built_1887.glb differs from the
 *     packed asset. ... delete it and run --materialize.
 *
 * Measured 2026-10-19, lap run 39360258127: #1116 had repacked Glessner, the lap merged
 * #1114's asset registries (T-2892) and then left #1114 alone at that refusal — which no run
 * could ever fix from the PR, because the stale file was the lap's own.
 *
 * WHAT IS REAL HERE AND WHAT IS FAKED. As in test_pr_lap_publish.mjs: the REAL
 * `.github/steward/pr-lap.sh`, real git, a real bare remote. publish.sh is a stub that does
 * exactly what the real one does with the package — materialize the output when it is
 * missing, refuse when it is present and differs — and recover_glessner_v4.py is a stub
 * exposing the real one's `targets()`. Case 2 cuts the refresh out of the lap and requires
 * the PR to be left alone with that refusal, so this suite is shown to see the fault.
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

function runLap({ lapSource = null } = {}) {
  const box = mkdtempSync(path.join(tmpdir(), 'prlappkg-'));
  const bare = path.join(box, 'remote.git');
  const work = path.join(box, 'work');
  const bin = path.join(box, 'bin');
  mkdirSync(bin, { recursive: true });
  git(box, 'init', '--quiet', '--bare', '-b', 'dev', bare);
  git(box, 'clone', '--quiet', bare, work);
  git(work, 'config', 'user.name', 'fixture');
  git(work, 'config', 'user.email', 'fixture@example.com');

  const app = path.join(work, 'chicago', '4d');
  const tools = path.join(app, 'tools');
  mkdirSync(tools, { recursive: true });
  mkdirSync(path.join(app, 'assets', 'gltf'), { recursive: true });
  writeFileSync(path.join(work, '.gitignore'), 'site/4d/\n');
  writeFileSync(path.join(app, '.gitignore'), '/assets/gltf/glessner.glb\n');
  writeFileSync(path.join(work, '.gitattributes'), '# no merge drivers in the fixture\n');
  writeFileSync(path.join(app, 'package.txt'), 'pack v1\n');
  writeFileSync(path.join(tools, 'recover_glessner_v4.py'),
    'def targets(root=None):\n    return ("assets/gltf/glessner.glb",)\n');
  // publish.sh's own first act, in miniature: materialize a missing output, refuse a stale one.
  writeFileSync(path.join(tools, 'publish.sh'), `#!/usr/bin/env bash
set -euo pipefail
out=assets/gltf/glessner.glb
if [ -e "$out" ] && ! cmp -s "$out" package.txt; then
  echo "Glessner v4 package: $out differs from the packed asset. delete it and run --materialize." >&2
  exit 1
fi
[ -e "$out" ] || cp package.txt "$out"
mkdir -p ../../site/4d && echo published
`);
  writeFileSync(path.join(tools, 'rederive.mjs'),
    "if (process.argv.includes('--resolvable')) process.exit(1);\nprocess.exit(0);\n");
  writeFileSync(path.join(tools, 'ticket.mjs'), 'process.exit(0);\n');
  writeFileSync(path.join(tools, 'stamp-changelog.mjs'), 'process.exit(0);\n');
  writeFileSync(path.join(tools, 'compile_scene.py'), 'pass\n');
  writeFileSync(path.join(tools, 'tickets.sh'), '#!/usr/bin/env bash\nexit 0\n');
  for (const f of ['publish.sh', 'tickets.sh']) chmodSync(path.join(tools, f), 0o755);
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'fixture: the tool tree and the package');
  git(work, 'push', '--quiet', 'origin', 'dev');

  git(work, 'checkout', '--quiet', '-b', 'steward/t-9999');
  writeFileSync(path.join(app, 'branch.md'), 'the branch its own work\n');
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'the PR');
  git(work, 'push', '--quiet', 'origin', 'steward/t-9999');
  const branchHead = git(work, 'rev-parse', 'HEAD').trim();

  // This clone published once already — its unpacked output is the v1 package's, and ignored.
  writeFileSync(path.join(app, 'assets', 'gltf', 'glessner.glb'), 'pack v1\n');

  git(work, 'checkout', '--quiet', 'dev');
  writeFileSync(path.join(app, 'package.txt'), 'pack v2\n');   // dev repacked Glessner
  git(work, 'commit', '--quiet', '-am', 'dev repacked the package');
  git(work, 'push', '--quiet', 'origin', 'dev');

  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
if [ "$1" = "api" ]; then printf '%b' '7\\tsteward/t-9999\\n'; fi
exit 0
`);
  chmodSync(path.join(bin, 'gh'), 0o755);
  let lap = LAP;
  if (lapSource !== null) { lap = path.join(box, 'pr-lap.sh'); writeFileSync(lap, lapSource); }
  const r = spawnSync('bash', [lap, '--repo', 'kevinrhaas/chicago'], {
    cwd: work, encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, GH_TOKEN: 'fake', LAP_BASE: 'dev', LAP_ONLY: '' },
  });
  const after = git(box, '--git-dir', bare, 'rev-parse', 'refs/heads/steward/t-9999').trim();
  let unpacked = null;
  try { unpacked = readFileSync(path.join(app, 'assets', 'gltf', 'glessner.glb'), 'utf8'); } catch { /* none */ }
  rmSync(box, { recursive: true, force: true });
  const out = `${r.stdout || ''}${r.stderr || ''}`;
  return { code: r.status, out, summary: (out.match(/^PR lap: .*$/m) || ['no summary line'])[0],
           moved: after !== branchHead, unpacked };
}

console.log('pr-lap.sh — the Glessner package is unpacked again from the merged tree (T-2907)');

/* 1. Dev repacked the package; the lap's unpacked copy is the old one. The lap pushes. */
{
  const r = runLap();
  check('the lap pushes', /pushed=1/.test(r.out), r.summary);
  check('…and the PR branch really moved on the remote', r.moved);
  check('…and publish never had to refuse a stale output', !/differs from the packed asset/.test(r.out));
  check('…and the unpacked output is now the MERGED package\'s', r.unpacked === 'pack v2\n', JSON.stringify(r.unpacked));
  check('the lap exits clean', r.code === 0, `exit ${r.code}`);
}

/* 2. The same suite with the refresh cut out — which is the lap as it stood on 2026-10-19. */
{
  const raw = readFileSync(LAP, 'utf8');
  const CALL = '  lap_refresh_package\n  ( cd chicago/4d && bash tools/publish.sh )';
  check('the refresh is called in one place, so cutting it is a fair simulation',
        raw.split(CALL).length === 2, `${raw.split(CALL).length - 1} occurrence(s)`);
  const r = runLap({ lapSource: raw.replace(CALL, '  ( cd chicago/4d && bash tools/publish.sh )') });
  check('without it the PR is left alone', /left-alone=1/.test(r.out), r.summary);
  check('…and the branch does not move', !r.moved);
  check('…for publish refusing the stale unpacked output', /differs from the packed asset/.test(r.out));
}

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);
