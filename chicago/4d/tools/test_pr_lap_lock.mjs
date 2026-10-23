#!/usr/bin/env node
/**
 * test_pr_lap_lock.mjs — the server lap and merge-ready leave a pull request alone
 * while a LIVE run holds its `lap/pr-<N>` lock, and read that lock exactly as
 * `ticket.mjs lap` takes it.
 *
 * WHY THIS EXISTS (T-2929). A run that laps a `resume` PR takes `lap/pr-<N>` first
 * (T-1721), and every RUN that looks is told the PR is a sibling's. The two server
 * sweeps never looked. On 2026-10-20 #1132's lock was taken at 13:00Z; pr-lap.sh
 * pushed df6ae544a over it at 13:19Z and merge-ready.sh merged that at 13:37Z, so the
 * holding run's merge of dev, its ten-minute re-derive, check.sh and smoke were all
 * thrown away.
 *
 * ONE DEFINITION OF "LIVE". Neither script re-derives the staleness rule: both ask
 * `ticket.mjs lap <N> --status`, which reads through the same `inspectMarker` and the
 * same `markerDead` that `lap` steals by. Section A holds that agreement directly —
 * whatever `--status` calls held, `lap` refuses; whatever it calls stale, `lap` steals.
 *
 * WHAT IS REAL AND WHAT IS FAKED. git is REAL, over REAL bare remotes; the locks are
 * taken by the REAL `ticket.mjs lap` or pushed as aged marker commits the way
 * test_ticket_claim_lock.mjs ages a claim. Both scripts are the REAL ones. `gh` is
 * faked. The lap's rebuild tools are stubs, as in test_pr_lap_current.mjs, and the
 * fixture's `tools/ticket.mjs` is the REAL source behind a one-line prelude that lets
 * every verb but `--status` exit 0 — so the lap's reconcile/prune/board are inert and
 * its lock read is the real code. Nothing here reaches the network.
 *
 * And each script is run once more with its lock read cut out, and the held case must
 * then FAIL — a regression test that cannot see the regression is decoration.
 */
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync, rmSync, readFileSync, cpSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const TICKET = path.join(HERE, 'ticket.mjs');
const STEWARD = path.resolve(HERE, '..', '..', '..', '.github', 'steward');
const LAP = path.join(STEWARD, 'pr-lap.sh');
const MERGE = path.join(STEWARD, 'merge-ready.sh');
const PR = 7;

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

const git = (cwd, ...args) => {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8' });
  if (r.status !== 0) throw new Error(`git ${args.join(' ')} in ${cwd}\n${r.stdout}${r.stderr}`);
  return r.stdout;
};

/** A run's clone: the REAL ticket.mjs, no tickets/ (so it loads none), origin = `remote`. */
function runClone(box, name, remote) {
  const repo = path.join(box, name);
  mkdirSync(path.join(repo, 'chicago', '4d', 'tools'), { recursive: true });
  cpSync(TICKET, path.join(repo, 'chicago', '4d', 'tools', 'ticket.mjs'));
  git(repo, 'init', '--quiet');
  git(repo, 'remote', 'add', 'origin', remote);
  return repo;
}
const tool = (repo, ...args) => {
  const r = spawnSync('node', [path.join(repo, 'chicago', '4d', 'tools', 'ticket.mjs'), ...args],
    { cwd: repo, encoding: 'utf8' });
  return { code: r.status, signal: r.signal, error: r.error?.message,
    out: `${r.stdout ?? ''}${r.stderr ?? ''}`.trim() };
};

/** The lock as a live run takes it: the REAL `ticket.mjs lap`, from a sibling clone. */
function takeLive(box, remote) {
  const sib = runClone(box, `sibling-${Math.random().toString(36).slice(2, 8)}`, remote);
  const r = tool(sib, 'lap', String(PR), '--by', 'sibling run');
  if (r.code !== 0) throw new Error(`could not take the fixture's live lock: ${r.out}`);
}

/** A dead run's lock: a marker commit dated `hours` ago (test_ticket_claim_lock's ageMarker). */
function plantAged(box, remote, hours) {
  const when = new Date(Date.now() - hours * 3600e3).toISOString();
  const env = { ...process.env, GIT_AUTHOR_DATE: when, GIT_COMMITTER_DATE: when,
    GIT_AUTHOR_NAME: 'old', GIT_AUTHOR_EMAIL: 'old@test', GIT_COMMITTER_NAME: 'old', GIT_COMMITTER_EMAIL: 'old@test' };
  const scratch = path.join(box, `aged-${hours}`);
  git(box, 'init', '--quiet', scratch);
  const tree = git(scratch, 'hash-object', '-w', '-t', 'tree', '/dev/null').trim();
  const aged = spawnSync('git', ['commit-tree', tree, '-m', `lap PR #${PR} — a run that died`], { cwd: scratch, encoding: 'utf8', env });
  if (aged.error || aged.status !== 0) {
    throw new Error(`could not create the aged marker: ${JSON.stringify({
      code: aged.status, signal: aged.signal, error: aged.error?.message,
      out: `${aged.stdout ?? ''}${aged.stderr ?? ''}`,
    })}`);
  }
  const c = aged.stdout.trim();
  git(scratch, 'push', '--quiet', '--force', remote, `${c}:refs/heads/lap/pr-${PR}`);
}

function setLock(box, remote, lock) {
  if (lock === 'live') takeLive(box, remote);
  else if (lock === 'stale') plantAged(box, remote, 4);      // past RUN_HOURS (3)
}

/* ============================================ A. the one reading, and its agreement */

console.log('ticket.mjs lap <N> --status — the reading both server sweeps ask for');
{
  const box = mkdtempSync(path.join(tmpdir(), 'laplock-a-'));
  const remote = path.join(box, 'origin.git');
  git(box, 'init', '--quiet', '--bare', remote);
  const me = runClone(box, 'me', remote);

  let r = tool(me, 'lap', String(PR), '--status');
  check('no marker reads FREE, exit 0', r.code === 0 && /^free lap\/pr-7\b/.test(r.out), `exit ${r.code}: ${r.out}`);

  takeLive(box, remote);
  r = tool(me, 'lap', String(PR), '--status');
  check('a lock a live run just took reads HELD, exit 3', r.code === 3 && /^held lap\/pr-7\b/.test(r.out), `exit ${r.code}: ${r.out}`);
  check('…naming who holds it', /sibling run/.test(r.out));
  const take = tool(me, 'lap', String(PR));
  check('…and `lap` itself refuses it — the two readings agree', take.code === 1 && /BEING LAPPED/.test(take.out),
        `exit ${take.code}`);

  plantAged(box, remote, 4);
  r = tool(me, 'lap', String(PR), '--status');
  check('a lock older than RUN_HOURS reads STALE, exit 0 — a dead run is no hold',
        r.code === 0 && /^stale lap\/pr-7\b/.test(r.out), `exit ${r.code}: ${r.out}`);
  const steal = tool(me, 'lap', String(PR));
  check('…and `lap` steals that same lock — the two readings agree', steal.code === 0 && /stole a dead lap/.test(steal.out),
        `exit ${steal.code}`);

  plantAged(box, remote, 2.5);
  r = tool(me, 'lap', String(PR), '--status');
  check('a lock 2.5h old is still inside the window and reads HELD', r.code === 3, `exit ${r.code}: ${r.out}`);

  git(me, 'remote', 'set-url', 'origin', path.join(box, 'no-such-remote.git'));
  r = tool(me, 'lap', String(PR), '--status');
  check('a remote that cannot answer reads UNKNOWN, exit 4 — never free, never held',
        r.code === 4 && /^unknown lap\/pr-7\b/.test(r.out), `exit ${r.code}: ${r.out}`);
  check('…with git\'s own reason', /does not appear to be a git repository|fatal/.test(r.out));
  rmSync(box, { recursive: true, force: true });
}

/* ========================================================= B. merge-ready.sh */

/**
 * merge-ready from a sandbox checkout: the REAL script and the REAL ticket.mjs beside
 * it, origin = a bare remote carrying `lock` (or no remote at all, `unreadable`), and
 * a fake `gh` that calls PR #7 `clean`. Returns whether it merged.
 */
function mergeReady({ lock = 'none', dry = '', source = null }) {
  const box = mkdtempSync(path.join(tmpdir(), 'laplock-b-'));
  const remote = path.join(box, 'origin.git');
  git(box, 'init', '--quiet', '--bare', remote);
  setLock(box, remote, lock);
  const checkout = runClone(box, 'checkout', lock === 'unreadable' ? path.join(box, 'gone.git') : remote);
  const copy = path.join(checkout, '.github', 'steward', 'merge-ready.sh');
  mkdirSync(path.dirname(copy), { recursive: true });
  writeFileSync(copy, source ?? readFileSync(MERGE, 'utf8'));
  const bin = path.join(box, 'bin');
  const merges = path.join(box, 'merges.txt');
  mkdirSync(bin, { recursive: true });
  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
for a in "$@"; do case "$a" in */merge) echo "$*" >> ${JSON.stringify(merges)}; exit 0 ;; esac; done
case "$*" in
  *"pulls?state=open"*) printf '${PR}\\n' ;;
  *".mergeable_state"*) echo clean ;;
  *".head.sha"*)        echo deadbeefdeadbeefdeadbeefdeadbeefdeadbeef ;;
  *".title"*)           echo "a resume pull request" ;;
esac
exit 0
`);
  chmodSync(path.join(bin, 'gh'), 0o755);
  const r = spawnSync('bash', [copy, '--repo', 'kevinrhaas/chicago'], {
    cwd: box, encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, GH_TOKEN: 'fake', MERGE_DRY_RUN: dry, MERGE_ONLY: '' },
  });
  const merged = existsSync(merges) && readFileSync(merges, 'utf8').includes(`pulls/${PR}/merge`);
  rmSync(box, { recursive: true, force: true });
  const out = `${r.stdout || ''}${r.stderr || ''}`;
  return { code: r.status, out, merged, summary: (out.match(/^merge-ready: .*$/m) || ['no summary'])[0] };
}

console.log('\nmerge-ready.sh — a clean PR a live run is lapping is not merged under it');
{
  const r = mergeReady({ lock: 'live' });
  check('a `clean` PR whose lap lock a live run holds is NOT merged — #1132 at 13:37Z', !r.merged, r.summary);
  check('…and the run says which run holds it', /BEING LAPPED by a live run/.test(r.out) && /sibling run/.test(r.out));
  check('…and counts it being-lapped, not refused', /refused=0 being-lapped=1/.test(r.summary), r.summary);
  check('…and exits clean: a held PR is not a failure', r.code === 0, `exit ${r.code}`);
}
{
  const r = mergeReady({ lock: 'stale' });
  check('a dead run\'s lock (older than RUN_HOURS) does not block the merge', r.merged, r.summary);
}
{
  const r = mergeReady({ lock: 'none' });
  check('no lock at all: merged, as before', r.merged, r.summary);
}
{
  const r = mergeReady({ lock: 'unreadable' });
  check('a lock that cannot be read is NOT merged on', !r.merged, r.summary);
  check('…and is reported as unreadable with ticket.mjs\'s reason, not as held',
        /lap lock cannot be read/.test(r.out) && /unknown \(exit 4\)/.test(r.out) && /refused=1 being-lapped=0/.test(r.summary),
        (r.out.match(/^#7 .*$/m) || [''])[0].slice(0, 160));
}
{
  const r = mergeReady({ lock: 'live', dry: '1' });
  check('a dry run says it would leave a held PR, not that it would merge it',
        !/WOULD MERGE/.test(r.out) && /BEING LAPPED/.test(r.out), r.summary);
}
{
  const raw = readFileSync(MERGE, 'utf8');
  const HEAD = 'lap_lock_free() {\n';
  check('merge-ready reads the lock in one function, so cutting it out is a fair simulation',
        raw.split(HEAD).length === 2, `${raw.split(HEAD).length - 1} definition(s)`);
  const r = mergeReady({ lock: 'live', source: raw.replace(HEAD, 'lap_lock_free() { return 0; }\nwas_lap_lock_free() {\n') });
  check('with the read cut out, the held PR IS merged — the suite sees the fault', r.merged, r.summary);
}

/* ============================================================ C. pr-lap.sh */

/**
 * The REAL lap over a REAL bare remote: PR #7's branch is one commit behind dev, so a
 * lap merges and pushes. `lock` is the state of lap/pr-7 when the lap starts;
 * `midLap` makes the stub rederive take a live lock DURING the lap, after the lap's
 * first read — #1132's shape, where the lock predated the push by nineteen minutes.
 */
function lap({ lock = 'none', midLap = false, noTool = false, source = null }) {
  const box = mkdtempSync(path.join(tmpdir(), 'laplock-c-'));
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
  writeFileSync(path.join(work, '.gitignore'), 'site/4d/\n');
  writeFileSync(path.join(work, '.gitattributes'), '# no merge drivers in the fixture\n');
  writeFileSync(path.join(app, 'data.json'), '{"town": 1}\n');

  // A sibling run, ready to take the lock from inside the lap if the case asks.
  const sibling = runClone(box, 'sibling', bare);
  const takeFromInside = midLap
    ? `import { pathToFileURL } from 'node:url';
// This clean fixture rebuilds once with --run, then once with --tail. Invoke
// the REAL CLI only on --run; a second take would correctly refuse the first.
if (process.argv.includes('--run')) {
  const savedCwd = process.cwd(), savedArgv = process.argv;
  const ticket = ${JSON.stringify(path.join(sibling, 'chicago', '4d', 'tools', 'ticket.mjs'))};
  process.chdir(${JSON.stringify(sibling)});
  process.argv = [process.execPath, ticket, 'lap', '${PR}', '--by', 'sibling run'];
  await import(pathToFileURL(ticket).href);
  process.chdir(savedCwd);
  process.argv = savedArgv;
}
`
    : '';
  writeFileSync(path.join(tools, 'rederive.mjs'), `${takeFromInside}console.log('[1/1] ok');\n`);
  writeFileSync(path.join(tools, 'publish.sh'), '#!/usr/bin/env bash\nmkdir -p ../../site/4d\necho published\n');
  // The REAL ticket.mjs, inert for every verb but `--status` (see the header).
  if (!noTool) {
    const [bang, ...rest] = readFileSync(TICKET, 'utf8').split('\n');
    writeFileSync(path.join(tools, 'ticket.mjs'),
      `${bang}\nif (!process.argv.includes('--status')) process.exit(0);\n${rest.join('\n')}`);
  }
  writeFileSync(path.join(tools, 'stamp-changelog.mjs'), 'process.exit(0);\n');
  writeFileSync(path.join(tools, 'compile_scene.py'), 'pass\n');
  writeFileSync(path.join(tools, 'tickets.sh'), '#!/usr/bin/env bash\nexit 0\n');
  for (const f of ['publish.sh', 'tickets.sh']) chmodSync(path.join(tools, f), 0o755);
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'fixture: the tool tree');
  git(work, 'push', '--quiet', 'origin', 'dev');

  git(work, 'checkout', '--quiet', '-b', 'claude/resume-1132');
  writeFileSync(path.join(app, 'pr.json'), '{"the": "pr"}\n');
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'the PR');
  git(work, 'push', '--quiet', 'origin', 'claude/resume-1132');
  const head = git(work, 'rev-parse', 'HEAD').trim();
  // dev moves on, so the branch is behind and a lap has something to push.
  git(work, 'checkout', '--quiet', 'dev');
  writeFileSync(path.join(app, 'dev.json'), '{"dev": "moved"}\n');
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'dev moves on');
  git(work, 'push', '--quiet', 'origin', 'dev');

  setLock(box, bare, lock);
  // Check THIS sandbox's premise, independently of section A's marker. Keep
  // the real status and refusal in a failed push assertion's diagnostics.
  const staleMarker = lock === 'stale' ? tool(sibling, 'lap', String(PR), '--status') : null;

  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
case "$*" in
  *check-runs*) echo ""; exit 0 ;;
  *pulls*) printf '%b' '${PR}\\tclaude/resume-1132\\n'; exit 0 ;;
esac
exit 0
`);
  chmodSync(path.join(bin, 'gh'), 0o755);
  let script = LAP;
  if (source !== null) { script = path.join(box, 'pr-lap.sh'); writeFileSync(script, source); }
  const r = spawnSync('bash', [script, '--repo', 'kevinrhaas/chicago'], {
    cwd: work, encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, GH_TOKEN: 'fake', LAP_BASE: 'dev', LAP_ONLY: '' },
  });
  const after = git(box, '--git-dir', bare, 'rev-parse', 'refs/heads/claude/resume-1132').trim();
  // Read from the outer test after the lap; the production lap only reads
  // markers, so this independently proves the rebuild created a real live one.
  const midLapMarker = midLap ? tool(sibling, 'lap', String(PR), '--status') : null;
  rmSync(box, { recursive: true, force: true });
  const out = `${r.stdout || ''}${r.stderr || ''}`;
  return { code: r.status, signal: r.signal, error: r.error?.message, out,
    moved: after !== head, head, after, staleMarker, midLapMarker,
    summary: (out.match(/^PR lap: .*$/m) || ['no summary'])[0] };
}

console.log('\npr-lap.sh — a PR a live run is lapping is left to that run');
{
  const r = lap({ lock: 'live' });
  check('a PR whose lap lock a live run holds is NOT pushed — #1132 at 13:19Z', !r.moved, r.summary);
  check('…and the lap says which run holds it', /BEING LAPPED by a live run/.test(r.out) && /sibling run/.test(r.out));
  check('…and spends nothing on it: no merge, no rebuild', !/regenerat|re-deriv|pushed [0-9a-f]/.test(r.out.split('BEING LAPPED')[1] ?? ''));
  check('…and counts it being-lapped, not left alone', /left-alone=0 being-lapped=1/.test(r.summary), r.summary);
  check('…and exits clean', r.code === 0, `exit ${r.code}`);
}
{
  const r = lap({ lock: 'stale' });
  check('the stale-lap sandbox really starts with a dead marker',
    r.staleMarker?.code === 0 && /^stale lap\/pr-7\b/.test(r.staleMarker.out),
    JSON.stringify(r.staleMarker));
  const pushed = r.code === 0 && !r.error && r.moved && /pushed=1/.test(r.summary);
  check('a dead run\'s lock does not block the lap: the PR is lapped and pushed',
    pushed, pushed ? r.summary : JSON.stringify(r));
}
{
  const r = lap({ lock: 'none' });
  check('no lock at all: lapped and pushed, as before', r.moved && /pushed=1/.test(r.summary), r.summary);
}
{
  const r = lap({ lock: 'none', midLap: true });
  check('the rebuild actually took a live sibling marker before judging the push guard',
        r.midLapMarker?.code === 3 && /^held lap\/pr-7\b/.test(r.midLapMarker.out)
          && /sibling run/.test(r.midLapMarker.out),
        r.midLapMarker ? `exit ${r.midLapMarker.code}: ${r.midLapMarker.out}` : 'missing fixture marker read');
  check('a lock taken WHILE the lap rebuilt stops the push — read again at the push',
        !r.moved && /took lap\/pr-7 while this lap rebuilt — NOT pushed/.test(r.out), r.summary);
  check('…and counts it being-lapped', /being-lapped=1/.test(r.summary), r.summary);
}
{
  const r = lap({ lock: 'live', noTool: true });
  check('a lap that cannot read the lock leaves the PR alone rather than lapping it blind',
        !r.moved && /lap lock UNREADABLE/.test(r.out) && /left-alone=1 being-lapped=0/.test(r.summary), r.summary);
  check('…and says why: the tool that reads it was not on dev', /could not be read from origin\/dev/.test(r.out));
}
{
  const raw = readFileSync(LAP, 'utf8');
  const HEAD = 'lap_lock_free() {\n';
  check('the lap reads the lock in one function, so cutting it out is a fair simulation',
        raw.split(HEAD).length === 2, `${raw.split(HEAD).length - 1} definition(s)`);
  const r = lap({ lock: 'live', source: raw.replace(HEAD, 'lap_lock_free() { return 0; }\nwas_lap_lock_free() {\n') });
  check('with the read cut out, the lap pushes over the live run — the suite sees the fault', r.moved, r.summary);
}

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);
