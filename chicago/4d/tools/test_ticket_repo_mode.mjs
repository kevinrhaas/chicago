#!/usr/bin/env node
/**
 * test_ticket_repo_mode.mjs — `ticket.mjs` against a tickets REPOSITORY of its own.
 *
 * Since 2026-09-23 the tickets live in kevinrhaas/chicago-tickets, cloned at tickets/,
 * and every command that changes one commits and pushes it to that repo's main (see the
 * REPO MODE note at the top of ticket.mjs). What that buys is only real if these hold,
 * so each is run for real — two clones of one bare repository, the tool copied into two
 * sandboxes shaped like the code repo, `gh` stubbed on PATH for the PR reads:
 *
 *   1. a claim is pushed the moment it is taken, and a second run's claim of the same
 *      ticket is REFUSED — whether it read before or after the first push;
 *   2. a claim older than the run window is stolen;
 *   3. `done` sets `review` and keeps the queue line; `settle` makes it `done` (queue
 *      line gone) once the PR has merged, and reopens it if the PR closed unmerged;
 *   4. new tickets land in their folder of 250, and a ticket id two writers minted at
 *      once is renumbered on the second push instead of landing twice;
 *   5. `ask` keeps the ticket in the queue with its question under its line, `list
 *      --workable` and `claim` step over it, and a claim after the answer drops the
 *      question line;
 *   6. `check` refuses a checkout with no tickets at all rather than passing it.
 */
import { mkdtempSync, mkdirSync, rmSync, writeFileSync, readFileSync, readdirSync, cpSync, existsSync, chmodSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
let failures = 0;
const check = (label, ok, detail = '') => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${label}${!ok && detail ? `\n        ${detail}` : ''}`);
  if (!ok) failures += 1;
};
const git = (cwd, ...a) => spawnSync('git', a, { cwd, encoding: 'utf8' });

const root = mkdtempSync(path.join(tmpdir(), 'c4d-repomode-'));
const bare = path.join(root, 'tickets.git');
const bin = path.join(root, 'bin');
const prs = path.join(root, 'prs.json');

function ticketText(id, title, extra = {}) {
  const fm = { id, title, state: 'open', epic: 'META', requested_by: 'owner', seen: false, effort: 'S',
    legacy_id: null, parent: null, opened: '2026-09-20', closed: null, pr: null, claimed_by: null,
    blocked_on: null, needs_bake: false, closed_at: null, claimed_run: null, ...extra };
  return `---\n${Object.entries(fm).map(([k, v]) => `${k}: ${v ?? 'null'}`).join('\n')}\n---\n\n${title}.\n\n**Acceptance:** it is done.\n`;
}

// The tickets repository: three open tickets in the queue, in the 1500 folder.
{
  const seed = path.join(root, 'seed');
  mkdirSync(path.join(seed, 'T-1500-1749'), { recursive: true });
  writeFileSync(path.join(seed, 'QUEUE.md'), '# QUEUE — top is next.\n\nT-1501 — first\nT-1502 — second\nT-1503 — third\n');
  writeFileSync(path.join(seed, 'QUEUE_ORDER.md'), '# RE-RANK LEDGER\n#   2026-09-20  seeded\n');
  writeFileSync(path.join(seed, '.gitignore'), 'BOARD.md\ntickets.json\n');
  for (const [id, title] of [['T-1501', 'first'], ['T-1502', 'second'], ['T-1503', 'third']]) {
    writeFileSync(path.join(seed, 'T-1500-1749', `${id}-${title}.md`), ticketText(id, title));
  }
  git(seed, 'init', '-q', '-b', 'main');
  git(seed, '-c', 'user.name=t', '-c', 'user.email=t@t', 'add', '-A');
  git(seed, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'seed');
  git(root, 'clone', '-q', '--bare', seed, bare);
}

// `gh` on PATH answers PR reads from prs.json; anything else fails like no network.
mkdirSync(bin, { recursive: true });
writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env node
const [,, sub, ...rest] = process.argv;
const url = rest.filter((a) => !a.startsWith('-') && !a.startsWith('Accept')).pop() || '';
const m = /pulls\\/(\\d+)$/.exec(url);
const all = JSON.parse(require('fs').readFileSync(${JSON.stringify(prs)}, 'utf8'));
if (sub !== 'api' || !m || !all[m[1]]) process.exit(1);
process.stdout.write(JSON.stringify(all[m[1]]));
`);
chmodSync(path.join(bin, 'gh'), 0o755);
writeFileSync(path.join(bin, 'curl'), '#!/bin/sh\nexit 7\n');
chmodSync(path.join(bin, 'curl'), 0o755);
writeFileSync(prs, '{}');

/** A code-repo-shaped sandbox with its own clone of the tickets repo. */
function sandbox(name) {
  const code = path.join(root, name);
  const app = path.join(code, 'chicago', '4d');
  mkdirSync(path.join(app, 'tools'), { recursive: true });
  cpSync(path.join(HERE, 'ticket.mjs'), path.join(app, 'tools', 'ticket.mjs'));
  git(code, 'init', '-q', '-b', 'dev');
  git(root, 'clone', '-q', bare, path.join(app, 'tickets'));
  git(path.join(app, 'tickets'), 'config', 'user.name', name);
  git(path.join(app, 'tickets'), 'config', 'user.email', `${name}@t`);
  return app;
}
const env = { ...process.env, PATH: `${bin}:${process.env.PATH}`, GITHUB_ACTIONS: '', GITHUB_RUN_ID: '',
  CHICAGO_TICKETS_DIR: '' };
delete env.CHICAGO_TICKETS_DIR;
const tool = (app, ...args) => spawnSync('node', [path.join(app, 'tools', 'ticket.mjs'), ...args],
  { cwd: app, encoding: 'utf8', env });
const remote = (file) => git(root, '--git-dir', bare, 'show', `main:${file}`).stdout;
const front = (text, key) => (new RegExp(`^${key}: (.*)$`, 'm').exec(text) || [])[1];

try {
  const A = sandbox('a');
  const B = sandbox('b');

  console.log('1. the claim is the lock');
  let r = tool(A, 'claim', 'T-1501', '--no-lock-note');
  check('run A claims T-1501', r.status === 0, r.stderr);
  check('…and the claim is on the remote at once', front(remote('T-1500-1749/T-1501-first.md'), 'state') === 'claimed');
  r = tool(B, 'claim', 'T-1501');
  check('run B, pulling after the push, is refused', r.status === 1 && /ALREADY CLAIMED/.test(r.stderr), r.stderr);
  // The race proper: B read BEFORE A pushed. Stage it by resetting B's clone to the seed.
  git(path.join(A, 'tickets'), 'pull', '-q', '--rebase', 'origin', 'main');
  r = tool(A, 'claim', 'T-1502');
  check('run A claims T-1502', r.status === 0, r.stderr);
  const bt = path.join(B, 'tickets');
  git(bt, 'fetch', '-q'); git(bt, 'reset', '-q', '--hard', 'origin/main~1');
  const text = readFileSync(path.join(bt, 'T-1500-1749', 'T-1502-second.md'), 'utf8');
  check('run B\'s stale tree still reads T-1502 open', front(text, 'state') === 'open');
  writeFileSync(path.join(bt, 'T-1500-1749', 'T-1502-second.md'),
    text.replace('state: open', 'state: claimed').replace('claimed_by: null', 'claimed_by: run b'));
  r = tool(B, 'sync', '-m', 'T-1502: claim (stale read)');
  check('a stale claim of the same ticket cannot land — the push conflicts and is refused',
    r.status === 1 && /NOT SAVED/.test(r.stderr), `${r.status} ${r.stderr}`);
  check('…and run A still holds it on the remote', /claimed_by: run /.test(remote('T-1500-1749/T-1502-second.md'))
    && !/claimed_by: run b/.test(remote('T-1500-1749/T-1502-second.md')));

  console.log('2. a dead claim is stolen');
  git(bt, 'pull', '-q', '--rebase', 'origin', 'main');
  const dead = path.join(bt, 'T-1500-1749', 'T-1503-third.md');
  writeFileSync(dead, readFileSync(dead, 'utf8').replace('state: open', 'state: claimed')
    .replace('claimed_by: null', 'claimed_by: run 9/1/2026, 1:00:00 AM CT'));
  tool(B, 'sync', '-m', 'an old claim');
  r = tool(A, 'claim', 'T-1503');
  check('a claim from three weeks ago is stolen', r.status === 0 && /stealing a dead claim/.test(r.stdout), r.stdout + r.stderr);

  console.log('3. done is review until the PR merges');
  r = tool(A, 'done', 'T-1501', '--pr', '41');
  const t1501 = remote('T-1500-1749/T-1501-first.md');
  check('done sets review with the PR', r.status === 0 && front(t1501, 'state') === 'review' && front(t1501, 'pr') === '41', r.stderr);
  check('…and keeps the queue line', /^T-1501\b/m.test(remote('QUEUE.md')));
  tool(A, 'done', 'T-1502', '--pr', '42');
  writeFileSync(prs, JSON.stringify({
    41: { number: 41, title: 'T-1501: first', state: 'closed', merged_at: '2026-09-23T15:00:00Z' },
    42: { number: 42, title: 'T-1502: second', state: 'closed', merged_at: null },
  }));
  r = tool(A, 'settle');
  const after1 = remote('T-1500-1749/T-1501-first.md');
  const after2 = remote('T-1500-1749/T-1502-second.md');
  check('settle: a merged PR makes its ticket done, closed on the merge instant',
    front(after1, 'state') === 'done' && front(after1, 'closed_at') === '2026-09-23T15:00:00Z', r.stdout + r.stderr);
  check('settle: …and takes its queue line', !/^T-1501\b/m.test(remote('QUEUE.md')));
  check('settle: a PR closed unmerged reopens its ticket with a note',
    front(after2, 'state') === 'open' && front(after2, 'pr') === 'null' && /was closed without merging/.test(after2));

  console.log('4. new tickets: the folder of 250, and a collision renumbered');
  r = tool(A, 'new', 'fourth', '--after', 'T-1502', '--by', 'loop');
  check('new lands in the folder its number belongs to',
    r.status === 0 && readdirSync(path.join(A, 'tickets', 'T-1500-1749')).some((f) => /^T-1504-fourth\.md$/.test(f)), r.stdout + r.stderr);
  // The race proper: B's `new` reads a tree from before A's T-1504 landed (its pull is
  // made to fail once, as an unlucky network would), mints T-1504 too, and only finds
  // out when its push is rejected. The rebase is clean — the files differ by slug — so
  // it is renumberCollisions, not git, that must catch it.
  git(bt, 'fetch', '-q'); git(bt, 'reset', '-q', '--hard', 'origin/main~1');
  const realGit = spawnSync('sh', ['-c', 'command -v git'], { encoding: 'utf8' }).stdout.trim();
  const flake = path.join(root, 'pull-flaked');
  writeFileSync(path.join(bin, 'git'), `#!/bin/sh
case "$*" in *" pull "*) if [ ! -e ${JSON.stringify(flake)} ]; then touch ${JSON.stringify(flake)}; echo "fatal: unable to access (injected)" >&2; exit 1; fi;; esac
exec ${JSON.stringify(realGit)} "$@"
`);
  chmodSync(path.join(bin, 'git'), 0o755);
  r = tool(B, 'new', 'fifth', '--by', 'loop');
  rmSync(path.join(bin, 'git'));
  const onRemote = git(root, '--git-dir', bare, 'ls-tree', '--name-only', 'main', 'T-1500-1749/').stdout;
  check('B minted on a stale read and was renumbered on push, not landed twice',
    /T-1504-fourth\.md/.test(onRemote) && /T-1505-fifth\.md/.test(onRemote) && !/T-1504-fifth/.test(onRemote)
    && /was taken by another writer meanwhile — this ticket is T-1505 now/.test(r.stdout), `${onRemote}\n${r.stdout}${r.stderr}`);
  check('…and its queue line was renumbered with it', /^T-1505 — fifth$/m.test(remote('QUEUE.md')) && !/^T-1504 — fifth/m.test(remote('QUEUE.md')));
  check('…and front matter agrees with the file name', front(remote('T-1500-1749/T-1505-fifth.md'), 'id') === 'T-1505');

  console.log('5. ask keeps the ticket in the queue, and the loop steps over it');
  git(path.join(A, 'tickets'), 'pull', '-q', '--rebase', 'origin', 'main');
  r = tool(A, 'ask', 'T-1502', '--question', 'Shingles or boards?', '--option', 'a=shingles',
    '--option', 'b=boards', '--rec', 'a', '--why', 'the 1834 view shows them');
  const q = remote('QUEUE.md');
  const asked = remote('T-1500-1749/T-1502-second.md');
  check('ask: decision pending, question and options in the ticket',
    r.status === 0 && front(asked, 'decision') === 'pending' && /## Decision needed/.test(asked)
    && /- \(a\) shingles/.test(asked) && /\*\*Recommendation:\*\* \(a\) shingles — the 1834 view/.test(asked), r.stderr);
  check('ask: the ticket keeps its queue line, with its question directly under it',
    /^T-1502\b.*\n#   \? T-1502 DECISION: Shingles or boards\? — \(a\) shingles  \(b\) boards — recommended: \(a\)$/m.test(q), q);
  const wl = tool(A, 'list', '--workable').stdout;
  check('list --workable leaves it out and names it as waiting on the owner',
    !/^T-1502 .*open/m.test(wl.split('WAITING ON THE OWNER')[0]) && /WAITING ON THE OWNER[\s\S]*T-1502/.test(wl), wl);
  r = tool(A, 'claim', 'T-1502');
  check('claim refuses a ticket waiting on the owner', r.status === 1 && /waiting on an owner decision/.test(r.stderr));
  const at = path.join(A, 'tickets', 'T-1500-1749', 'T-1502-second.md');
  writeFileSync(at, readFileSync(at, 'utf8').replace('decision: pending', 'decision: answered')
    .replace('decision_answer: null', 'decision_answer: b'));
  tool(A, 'sync', '-m', 'owner answered');
  r = tool(A, 'claim', 'T-1502');
  check('once answered it is claimable, and the claim drops the question line',
    r.status === 0 && !/\? T-1502 DECISION/.test(remote('QUEUE.md')), r.stderr);
  const board = JSON.parse(readFileSync(path.join(A, 'tickets', 'tickets.json'), 'utf8'));
  const b1501 = board.tickets.find((t) => t.id === 'T-1501');
  check('tickets.json carries each ticket\'s path and PR url',
    b1501?.path === 'T-1500-1749/T-1501-first.md' && /\/kevinrhaas\/chicago\/pull\/41$/.test(b1501?.pr_url || ''), JSON.stringify(b1501));

  console.log('5b. sync: a hand edit pushes under its own message, and a dirty clone still pulls');
  const hand = path.join(A, 'tickets', 'T-1500-1749', 'T-1503-third.md');
  writeFileSync(hand, readFileSync(hand, 'utf8') + '\nA finding added by hand.\n');
  r = tool(A, 'sync', '-m', 'T-1503: a finding');
  check('sync -m names the commit, and does not try to pull over the edit',
    r.status === 0 && !/could not pull/.test(r.stderr)
    && git(root, '--git-dir', bare, 'log', '-1', '--format=%s', 'main').stdout.trim() === 'T-1503: a finding', r.stdout + r.stderr);
  tool(A, 'ask', 'T-1503', '--question', 'Keep it?', '--option', 'a=yes', '--option', 'b=no');
  const chk2 = tool(A, 'check');
  check('check counts an asked decision as waiting on the owner', /\b[1-9]\d* waiting on the owner/.test(chk2.stdout), chk2.stdout);

  console.log('6. no tickets is a failure, not a pass');
  const empty = path.join(root, 'empty', 'chicago', '4d');
  mkdirSync(path.join(empty, 'tools'), { recursive: true });
  cpSync(path.join(HERE, 'ticket.mjs'), path.join(empty, 'tools', 'ticket.mjs'));
  r = tool(empty, 'check');
  check('check with no tickets/ at all fails and names the fix', r.status === 1 && /tickets\.sh/.test(r.stderr), r.stderr);
} finally {
  rmSync(root, { recursive: true, force: true });
}
console.log(failures ? `\ntest_ticket_repo_mode: ${failures} FAILED` : '\ntest_ticket_repo_mode: all hold');
process.exit(failures ? 1 : 0);
