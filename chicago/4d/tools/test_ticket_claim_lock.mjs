#!/usr/bin/env node
/**
 * test_ticket_claim_lock.mjs — a claim is a LOCK on the remote, taken at claim
 * time, and two runs cannot hold one ticket.
 *
 * WHY THIS EXISTS (owner, 2026-09-11: "can you prevent duplicate claiming going
 * forward?"). On that morning six open PRs turned out to be six runs working
 * tickets another run had already finished. The cause was not merging and not
 * the queue: `claim` writes to a ticket FILE, which reaches `dev` only when its
 * PR merges, and the one shared signal a run could see — a pushed branch —
 * appears about an hour after the claim. T-1026's loser claimed 24 minutes after
 * its winner and 77 minutes before the winner pushed anything.
 *
 * A lock is worth nothing unless it is exercised against a real remote, so every
 * case here runs `ticket.mjs` twice against a real bare repository and reads what
 * the second run is told. The failure modes a lock like this can have, each
 * asserted below:
 *
 *   1. IT DOES NOT ACTUALLY LOCK — the second claim prints a warning and carries
 *      on. Asserted by exit status, not by the message.
 *   2. IT LOCKS TOO HARD — a remote that cannot be reached stops the run. That
 *      turns every network blip into a dead slice, and it is the property the
 *      branch scan always had and must keep: no remote ⇒ claim succeeds.
 *   3. IT STRANDS A TICKET — a run dies holding a claim and nobody can ever take
 *      it again. A marker older than RUN_HOURS must be stolen automatically.
 *   4. IT STEALS A LIVE ONE — a claim younger than RUN_HOURS is never stolen.
 *   5. THE STEAL ITSELF RACES — two runs stealing one dead claim both win. The
 *      steal leases on the sha the marker holds, so exactly one can succeed;
 *      asserted directly against the remote with a stale expected value.
 *   6. IT NEVER LETS GO — `done` leaves the marker behind, so the ticket's id is
 *      locked forever and the next run to touch it is refused.
 *   7. IT NEEDS A CONFIGURED GIT USER — `commit-tree` dies `fatal: empty ident
 *      name` on a fresh runner. That is not hypothetical: it is the bug that
 *      silently broke every PR lap until 2026-09-10, so it is asserted with the
 *      identity removed from the config entirely.
 *
 * EVERYTHING RUNS IN A SANDBOX, as test_ticket_restamp.mjs explains: the tool
 * resolves its paths from its own location, so a temporary tree beside a copy of
 * the tool is a whole world for it to be wrong in, and the real queue and the
 * real origin are never touched.
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

/* ------------------------------------------------------------------ fixture */

const TICKET = (id) => `---
id: ${id}
title: a ticket to contend for
state: open
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-11
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

a ticket to contend for.

**Acceptance:** fixture.
`;

const git = (cwd, args, env) =>
  spawnSync('git', args, { cwd, encoding: 'utf8', env: { ...process.env, ...env } });

/**
 * One sandbox = a bare "origin" plus N independent clones, each a run. The tool
 * is copied in beside a tickets/ tree so it resolves ROOT to the sandbox.
 */
function sandbox({ runs = 2, id = 'T-0001', identity = true } = {}) {
  const root = mkdtempSync(path.join(tmpdir(), 'claimlock-'));
  const origin = path.join(root, 'origin.git');
  execFileSync('git', ['init', '-q', '--bare', origin]);

  const clones = [];
  for (let i = 0; i < runs; i += 1) {
    const app = path.join(root, `run${i}`, 'chicago', '4d');
    mkdirSync(path.join(app, 'tools'), { recursive: true });
    mkdirSync(path.join(app, 'tickets'), { recursive: true });
    for (const f of ['ticket.mjs']) cpSync(path.join(HERE, f), path.join(app, 'tools', f));
    writeFileSync(path.join(app, 'tickets', `${id}-a-ticket-to-contend-for.md`), TICKET(id));
    writeFileSync(path.join(app, 'tickets', 'QUEUE.md'), `# QUEUE\n\n${id} — a ticket to contend for\n`);

    const repo = path.join(root, `run${i}`);
    git(repo, ['init', '-q', '-b', 'main']);
    if (identity) {
      git(repo, ['config', 'user.email', `run${i}@test`]);
      git(repo, ['config', 'user.name', `run${i}`]);
    }
    git(repo, ['remote', 'add', 'origin', origin]);
    clones.push(repo);
  }
  return { root, origin, clones };
}

/** Run the tool as one of the clones. Returns { code, out }. */
function claim(repo, id, extra = [], env) {
  const r = spawnSync('node', [path.join(repo, 'chicago', '4d', 'tools', 'ticket.mjs'),
    'claim', id, ...extra], { cwd: repo, encoding: 'utf8', env: { ...process.env, ...env } });
  return { code: r.status, out: `${r.stdout ?? ''}${r.stderr ?? ''}` };
}

/** Age a marker by rewriting it as a commit with an older date. */
function ageMarker(repo, origin, id, hoursAgo) {
  const when = new Date(Date.now() - hoursAgo * 3600 * 1000).toISOString();
  const tree = git(repo, ['hash-object', '-w', '-t', 'tree', '/dev/null']).stdout.trim();
  const c = git(repo, ['commit-tree', tree, '-m', `claim ${id} — an older run`], {
    GIT_AUTHOR_DATE: when, GIT_COMMITTER_DATE: when,
    GIT_AUTHOR_NAME: 'old', GIT_AUTHOR_EMAIL: 'old@test',
    GIT_COMMITTER_NAME: 'old', GIT_COMMITTER_EMAIL: 'old@test',
  }).stdout.trim();
  git(repo, ['push', '--force', origin, `${c}:refs/heads/claim/${id.toLowerCase()}`]);
  return c;
}

const markerSha = (repo, origin, id) =>
  (git(repo, ['ls-remote', origin, `refs/heads/claim/${id.toLowerCase()}`]).stdout || '')
    .split('\t')[0].trim();

/** The run window ticket.mjs sweeps past — kept in step with RUN_HOURS there. */
const RUN_HOURS = 3;

/* -------------------------------------------------------------------- cases */

console.log('claim lock');
const boxes = [];

/* 1. a second run is REFUSED, and refused by exit status. */
{
  const s = sandbox(); boxes.push(s.root);
  const first = claim(s.clones[0], 'T-0001');
  const second = claim(s.clones[1], 'T-0001');
  check('the first run claims', first.code === 0, first.out.trim().split('\n').pop());
  check('the second run is REFUSED', second.code !== 0, `exit ${second.code}`);
  check('and is told who holds it, not just that something does',
    /ALREADY CLAIMED/.test(second.out) && /claim\/t-0001/.test(second.out));
  check('and is pointed at the next workable ticket',
    /list --workable/.test(second.out));
}

/* 1b. TWO RUNS IN THE SAME SECOND, with identical claim text — the case the lock
 *     exists for, and the one it got wrong first time. A commit object is a pure
 *     function of its content, so without a nonce both runs build the SAME sha,
 *     the second push answers `Everything up-to-date`, exit 0, and BOTH runs
 *     believe they hold the ticket. `--by` is pinned so the two claim lines are
 *     byte-identical; only the nonce can separate them. */
{
  const s = sandbox(); boxes.push(s.root);
  const a = claim(s.clones[0], 'T-0001', ['--by', 'run']);
  const b = claim(s.clones[1], 'T-0001', ['--by', 'run']);
  check('identical claims in one second: exactly one wins',
    [a.code, b.code].filter((c) => c === 0).length === 1, `exits ${a.code}/${b.code}`);
  check('and the loser is refused, not told it won',
    /ALREADY CLAIMED/.test(b.out) || /ALREADY CLAIMED/.test(a.out));
}

/* 2. an UNREACHABLE remote never stops a run. */
{
  const s = sandbox({ runs: 1 }); boxes.push(s.root);
  git(s.clones[0], ['remote', 'set-url', 'origin', path.join(s.root, 'nope.git')]);
  const r = claim(s.clones[0], 'T-0001');
  check('no reachable remote ⇒ the claim still succeeds', r.code === 0, `exit ${r.code}`);
  check('and says so rather than pretending it locked',
    /claim lock not taken/.test(r.out), r.out.trim().split('\n')[0]);
}

/* 3. a DEAD claim is stolen. */
{
  const s = sandbox(); boxes.push(s.root);
  ageMarker(s.clones[0], s.origin, 'T-0001', 9);
  const r = claim(s.clones[1], 'T-0001');
  check('a claim older than a run is stolen', r.code === 0, `exit ${r.code}`);
  check('and the steal is reported, never silent', /stole a dead claim/.test(r.out));
}

/* 4. a LIVE claim is not stolen, however much the second run would like it. */
{
  const s = sandbox(); boxes.push(s.root);
  ageMarker(s.clones[0], s.origin, 'T-0001', 1);
  const r = claim(s.clones[1], 'T-0001');
  check('a claim younger than a run is NOT stolen', r.code !== 0, `exit ${r.code}`);
  check('--force takes it anyway', claim(s.clones[1], 'T-0001', ['--force']).code === 0);
}

/* 5. two runs stealing ONE dead claim: the lease decides, and only one wins. */
{
  const s = sandbox(); boxes.push(s.root);
  const dead = ageMarker(s.clones[0], s.origin, 'T-0001', 9);
  const stolen = claim(s.clones[1], 'T-0001');           // run 1 steals it
  const now = markerSha(s.clones[1], s.origin, 'T-0001');
  // Run 2 arrives with the sha it read BEFORE run 1's steal — the stale lease.
  const tree = git(s.clones[0], ['hash-object', '-w', '-t', 'tree', '/dev/null']).stdout.trim();
  const mine = git(s.clones[0], ['commit-tree', tree, '-m', 'claim T-0001 — late run']).stdout.trim();
  const race = git(s.clones[0], ['push', s.origin, `${mine}:refs/heads/claim/t-0001`,
    `--force-with-lease=refs/heads/claim/t-0001:${dead}`]);
  check('the first stealer wins', stolen.code === 0 && now !== dead);
  check('a stealer holding the OLD sha is rejected by the server', race.status !== 0,
    (race.stderr || '').split('\n').find((l) => /rejected/.test(l))?.trim());
  check('and the marker still belongs to the winner',
    markerSha(s.clones[0], s.origin, 'T-0001') === now);
}

/* 6. `done` LETS GO, so the id is not locked forever. */
{
  const s = sandbox(); boxes.push(s.root);
  claim(s.clones[0], 'T-0001');
  check('the marker exists while the work is in flight',
    markerSha(s.clones[0], s.origin, 'T-0001') !== '');
  spawnSync('node', [path.join(s.clones[0], 'chicago', '4d', 'tools', 'ticket.mjs'),
    'done', 'T-0001', '--pr', '1'], { cwd: s.clones[0], encoding: 'utf8' });
  check('`done` releases it', markerSha(s.clones[0], s.origin, 'T-0001') === '');
  check('so the ticket can be claimed again', claim(s.clones[1], 'T-0001', ['--force']).code === 0);
}

/* 7. NO CONFIGURED GIT IDENTITY — the pr-lap bug, asserted so it cannot return. */
{
  const s = sandbox({ identity: false }); boxes.push(s.root);
  const r = claim(s.clones[0], 'T-0001', [], {
    GIT_AUTHOR_NAME: '', GIT_AUTHOR_EMAIL: '',
    GIT_COMMITTER_NAME: '', GIT_COMMITTER_EMAIL: '',
    HOME: s.root, XDG_CONFIG_HOME: s.root, GIT_CONFIG_GLOBAL: '/dev/null',
  });
  check('a runner with no git identity still takes the lock', r.code === 0, `exit ${r.code}`);
  check('and really did write a marker', markerSha(s.clones[0], s.origin, 'T-0001') !== '');
  check('so a second run there is still refused', claim(s.clones[1], 'T-0001').code !== 0);
}

/* 8. --no-lock is an escape for a checkout with no remote, not a way past a live claim. */
{
  const s = sandbox(); boxes.push(s.root);
  claim(s.clones[0], 'T-0001');
  const r = claim(s.clones[1], 'T-0001', ['--no-lock']);
  check('--no-lock skips the lock entirely', r.code === 0, `exit ${r.code}`);
  check('and leaves the holder\'s marker untouched',
    markerSha(s.clones[1], s.origin, 'T-0001') !== '');
}

/* 9. `split` KEEPS ITS MARKER — REVERSED on 2026-09-17, and both faults are here.
 *
 * It used to release, and the reason was real: of nineteen markers standing on
 * kevinrhaas/custom on 2026-09-14, THIRTEEN belonged to tickets in state `split`.
 * That was right about the litter and wrong about the lock, and T-1145 is the bill:
 *
 *   03:38:16  run A claims T-1145, splits it, and the release deletes claim/t-1145
 *             while run A's own PR is still unopened.
 *   03:57:43  run B reads `dev`, where the split has not landed and T-1145 is still
 *             `open` at the top of the queue, finds no lock, and claims it.
 *
 * Both split it into different children and built the same feature twice with
 * colliding ids. A split is NOT finished work like `done`: the run carries on for
 * another hour on a child, so `dev` goes on offering the parent for that whole hour.
 * That is the widest window any terminal state has.
 *
 * The litter is collected by AGE instead, which is the second half of this case:
 * `claims --sweep` takes any marker past the run window, and the lap runs it. So a
 * marker outlives its run by at most a sweep, and the lock lives exactly as long as
 * the work is unmerged. `tools/test_ticket_claim_split.mjs` holds the other half —
 * that a second claim on the split parent is actually refused. */
{
  const s = sandbox(); boxes.push(s.root);
  claim(s.clones[0], 'T-0001');
  check('the marker exists while the work is in flight',
    markerSha(s.clones[0], s.origin, 'T-0001') !== '');
  const r = spawnSync('node', [path.join(s.clones[0], 'chicago', '4d', 'tools', 'ticket.mjs'),
    'split', 'T-0001', 'the first piece', 'the second piece'],
    { cwd: s.clones[0], encoding: 'utf8' });
  check('`split` succeeds', r.status === 0, (r.stderr || '').trim().split('\n').pop());
  check('`split` KEEPS the marker — the parent is still offered by an unmerged dev',
    markerSha(s.clones[0], s.origin, 'T-0001') !== '',
    'released — a second run can claim the ticket it just split');
}

/* 9b. …and the litter that made `split` release is swept by age instead. */
{
  const s = sandbox(); boxes.push(s.root);
  ageMarker(s.clones[0], s.origin, 'T-0001', RUN_HOURS + 2);
  check('a marker older than a run stands until somebody sweeps',
    markerSha(s.clones[0], s.origin, 'T-0001') !== '');
  const r = spawnSync('node', [path.join(s.clones[0], 'chicago', '4d', 'tools', 'ticket.mjs'),
    'claims', '--sweep'], { cwd: s.clones[0], encoding: 'utf8' });
  check('`claims --sweep` collects it, which is what the lap runs every pass',
    r.status === 0 && markerSha(s.clones[0], s.origin, 'T-0001') === '',
    (r.stdout || '').trim().split('\n').pop());
}

for (const b of boxes) rmSync(b, { recursive: true, force: true });

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);
