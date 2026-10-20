#!/usr/bin/env node
/**
 * test_ticket_group.mjs — a run claims a GROUP of tickets and ships them in one PR (T-2938).
 *
 * Owner, 2026-10-20: "when claiming a ticket, it can and should evaluate if it can claim
 * multiple and handle them as a group in a single PR that way we minimize PR churn".
 * Run for real against a tickets repository of its own (two clones of one bare repo, the
 * tool copied into code-repo-shaped sandboxes, no network), as test_ticket_repo_mode.mjs
 * does:
 *
 *   1. `claim A B C` with B held live by another run claims A and C in ONE commit,
 *      reports B with the single claim's own reason, exits 0, and records the group on
 *      A and C only;
 *   2. a group whose every member is refused exits non-zero and changes nothing;
 *   3. a member another run claims between this run's read and its push is reported as
 *      taken and the rest are claimed on the next round (the compare-and-swap holds);
 *   4. `done A C --pr N` sets both to review on PR N in one commit — and a guard that
 *      refuses one member leaves EVERY member as it was;
 *   5. `release` gives a claim back to `open` with the reason in the body, drops it from
 *      its mates' group, and refuses a ticket that is not claimed;
 *   6. the `group` field round-trips (front matter, tickets.json, BOARD.md) and a ticket
 *      never grouped carries no such line;
 *   7. a single id claims, refuses and closes exactly as before;
 *   8. a group on one house is one run on it: `claim T-C --with T-A` grows the group the run
 *      holds, while another run — or one merely sharing the run URL — is held off;
 *   9. `list --workable --group` offers a linked ticket and never an L, a pending decision,
 *      a live claim or a band-only neighbour.
 */
import { mkdtempSync, mkdirSync, rmSync, writeFileSync, readFileSync, cpSync, chmodSync } from 'node:fs';
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

const root = mkdtempSync(path.join(tmpdir(), 'c4d-group-'));
const bare = path.join(root, 'tickets.git');
const bin = path.join(root, 'bin');

function ticketText(id, title, extra = {}, body = '') {
  const fm = { id, title, state: 'open', epic: 'META', requested_by: 'owner', seen: false, effort: 'S',
    legacy_id: null, parent: null, opened: '2026-10-20', closed: null, pr: null, claimed_by: null,
    blocked_on: null, needs_bake: false, closed_at: null, claimed_run: null, ...extra };
  return `---\n${Object.entries(fm).map(([k, v]) => `${k}: ${v ?? 'null'}`).join('\n')}\n---\n\n${title}.\n\n${body}**Acceptance:** it is done.\n`;
}

const live = `run ${new Date(Date.now() - 20 * 60e3).toLocaleString('en-US', { timeZone: 'America/Chicago' })} CT`;
const liveAt = new Date(Date.now() - 20 * 60e3).toISOString();
const TICKETS = [
  // band 1: a group of three, the middle one held live by another run
  ['T-1701', 'alpha', {}],
  ['T-1702', 'bravo', { state: 'claimed', claimed_by: live, claimed_at: liveAt, claimed_run: 'https://example/runs/9' }],
  ['T-1703', 'charlie', {}],
  // band 1: every member refused (an L, a pending decision, a finished ticket)
  ['T-1704', 'delta', { effort: 'L' }],
  ['T-1705', 'echo', { decision: 'pending' }],
  ['T-1706', 'foxtrot', { state: 'done', pr: 7, closed: '2026-10-19', closed_at: '2026-10-19T12:00:00Z' }],
  // band 2: the race
  ['T-1711', 'golf', {}],
  ['T-1712', 'hotel', {}],
  ['T-1713', 'india', {}],
  // band 3: single-id behaviour, and an image-gated ticket for the atomic done
  ['T-1721', 'juliet', {}],
  ['T-1722', 'kilo', {}, '## Image gate\n\n- views: none committed\n\n'],
  // band 4: one house (1801), worked by one run
  ['T-1731', "1801 Prairie's frieze", { epic: 'SOUTH_TIME' }],
  ['T-1732', "1801 Prairie's pilasters", { epic: 'SOUTH_TIME' }],
  ['T-1733', "Kimball's loggia", { epic: 'SOUTH_TIME' }],
  // band 5: the shortlist
  ['T-1741', 'the anchor: the navigator panel', {}, 'Touches `navigator.js` and nav_panel.css.\n\n'],
  ['T-1742', 'shares the file', {}, 'Also edits navigator.js.\n\n'],
  ['T-1743', 'names the anchor', {}, 'Waits on T-1741 for its panel.\n\n'],
  ['T-1744', 'an L on the same file', { effort: 'L' }, 'Rewrites navigator.js.\n\n'],
  ['T-1745', 'a pending decision on the same file', { decision: 'pending' }, 'navigator.js again.\n\n'],
  ['T-1746', 'a live claim on the same file',
    { state: 'claimed', claimed_by: live, claimed_at: liveAt }, 'navigator.js once more.\n\n'],
  ['T-1747', 'only a neighbour in the band', {}, 'Nothing in common.\n\n'],
];

{
  const seed = path.join(root, 'seed');
  mkdirSync(path.join(seed, 'T-1500-1749'), { recursive: true });
  const bands = new Map();
  for (const [id, title] of TICKETS) {
    const b = Number(id.slice(4, 5));   // T-17B? → band B
    if (!bands.has(b)) bands.set(b, []);
    if (!['T-1706'].includes(id)) bands.get(b).push(`${id} — ${title}`);
  }
  const queue = [...bands].map(([b, rows]) => `# --- ${b}. BAND ${b}\n${rows.join('\n')}`).join('\n\n');
  writeFileSync(path.join(seed, 'QUEUE.md'), `# QUEUE — top is next.\n\n${queue}\n`);
  writeFileSync(path.join(seed, 'QUEUE_ORDER.md'), '# RE-RANK LEDGER\n#   2026-10-20  seeded\n');
  writeFileSync(path.join(seed, '.gitignore'), 'BOARD.md\ntickets.json\n');
  for (const [id, title, extra, body] of TICKETS) {
    writeFileSync(path.join(seed, 'T-1500-1749', `${id}-${id.slice(2)}.md`), ticketText(id, title, extra, body));
  }
  git(seed, 'init', '-q', '-b', 'main');
  git(seed, '-c', 'user.name=t', '-c', 'user.email=t@t', 'add', '-A');
  git(seed, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'seed');
  git(root, 'clone', '-q', '--bare', seed, bare);
}

// No network: `gh` and `curl` fail, so the open PR list reads as unreadable (a note).
mkdirSync(bin, { recursive: true });
writeFileSync(path.join(bin, 'gh'), '#!/bin/sh\nexit 1\n');
writeFileSync(path.join(bin, 'curl'), '#!/bin/sh\nexit 7\n');
chmodSync(path.join(bin, 'gh'), 0o755);
chmodSync(path.join(bin, 'curl'), 0o755);

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
const baseEnv = { ...process.env, PATH: `${bin}:${process.env.PATH}`, GITHUB_ACTIONS: '', GITHUB_RUN_ID: '',
  GITHUB_SERVER_URL: '', GITHUB_REPOSITORY: '' };
delete baseEnv.CHICAGO_TICKETS_DIR;
const tool = (app, args, env = {}) => spawnSync('node', [path.join(app, 'tools', 'ticket.mjs'), ...args],
  { cwd: app, encoding: 'utf8', env: { ...baseEnv, ...env } });
const remote = (id) => git(root, '--git-dir', bare, 'show', `main:T-1500-1749/${id}-${id.slice(2)}.md`).stdout;
const front = (text, key) => (new RegExp(`^${key}: (.*)$`, 'm').exec(text) || [])[1];
const head = () => git(root, '--git-dir', bare, 'rev-parse', 'main').stdout.trim();
const subject = () => git(root, '--git-dir', bare, 'log', '-1', '--format=%s', 'main').stdout.trim();
const runEnv = (n) => ({ GITHUB_SERVER_URL: 'https://github.com', GITHUB_REPOSITORY: 'o/r', GITHUB_RUN_ID: String(n) });

try {
  const A = sandbox('a');
  const B = sandbox('b');

  console.log('1. a group of three with one held live: two claimed, one reported');
  let before = head();
  let r = tool(A, ['claim', 'T-1701', 'T-1702', 'T-1703']);
  check('exit 0 — the group shrank, it did not fail', r.status === 0, r.stdout + r.stderr);
  check('T-1701 and T-1703 are claimed on the remote',
    front(remote('T-1701'), 'state') === 'claimed' && front(remote('T-1703'), 'state') === 'claimed');
  check('…in ONE commit, whose message names both and the group',
    git(root, '--git-dir', bare, 'rev-list', '--count', `${before}..main`).stdout.trim() === '1'
    && /^T-1701, T-1703: claim — .*\(one group, one PR\)$/.test(subject()), subject());
  check('T-1702 is reported with the single claim\'s own reason, and left to its holder',
    /T-1702 NOT CLAIMED:[\s\S]*T-1702 IS ALREADY CLAIMED/.test(r.stderr)
    && front(remote('T-1702'), 'claimed_run') === 'https://example/runs/9', r.stderr);
  check('the summary says 2 of 3 and how to ship them',
    /claimed 2 of 3: T-1701, T-1703 — refused: T-1702/.test(r.stdout)
    && /done T-1701 T-1703 --pr N/.test(r.stdout) && /steward\/t1701-t1703-/.test(r.stdout), r.stdout);
  check('each member records the group of what was actually claimed',
    front(remote('T-1701'), 'group') === 'T-1701,T-1703' && front(remote('T-1703'), 'group') === 'T-1701,T-1703'
    && front(remote('T-1702'), 'group') === undefined);

  console.log('2. every member refused: non-zero, nothing written');
  before = head();
  r = tool(A, ['claim', 'T-1704', 'T-1705', 'T-1706']);
  check('exit 1 when none was claimed', r.status === 1, r.stdout + r.stderr);
  check('…each refusal says why (L, decision, done)',
    /T-1704 is effort L/.test(r.stderr) && /T-1705 is waiting on an owner decision/.test(r.stderr)
    && /T-1706 is done, not claimable/.test(r.stderr) && /claimed 0 of 3/.test(r.stdout), r.stderr);
  check('…and the remote did not move', head() === before);

  console.log('3. a member taken between the read and the push is reported, the rest claimed');
  // B reads a tree from before A's claim of T-1712: its pull is made to fail once.
  git(path.join(B, 'tickets'), 'pull', '-q', '--rebase', 'origin', 'main');
  r = tool(A, ['claim', 'T-1712'], runEnv(111));
  check('run A claims T-1712 alone', r.status === 0 && /^T-1712 claimed$/m.test(r.stdout), r.stdout + r.stderr);
  const realGit = spawnSync('sh', ['-c', 'command -v git'], { encoding: 'utf8' }).stdout.trim();
  const flake = path.join(root, 'pull-flaked');
  writeFileSync(path.join(bin, 'git'), `#!/bin/sh
case "$*" in *" pull "*) if [ ! -e ${JSON.stringify(flake)} ]; then touch ${JSON.stringify(flake)}; echo "fatal: unable to access (injected)" >&2; exit 1; fi;; esac
exec ${JSON.stringify(realGit)} "$@"
`);
  chmodSync(path.join(bin, 'git'), 0o755);
  r = tool(B, ['claim', 'T-1711', 'T-1712', 'T-1713'], runEnv(222));
  rmSync(path.join(bin, 'git'));
  check('run B, on a stale read, still ends with T-1711 and T-1713 claimed',
    r.status === 0 && front(remote('T-1711'), 'state') === 'claimed' && front(remote('T-1713'), 'state') === 'claimed'
    && front(remote('T-1711'), 'claimed_run') === 'https://github.com/o/r/actions/runs/222', r.stdout + r.stderr);
  check('…T-1712 reported as taken, still run A\'s',
    /asking the group again/.test(r.stderr) && /T-1712 NOT CLAIMED:[\s\S]*ALREADY CLAIMED/.test(r.stderr)
    && front(remote('T-1712'), 'claimed_run') === 'https://github.com/o/r/actions/runs/111', r.stderr);
  check('…and the group is the two it holds', front(remote('T-1711'), 'group') === 'T-1711,T-1713');

  console.log('4. done A C --pr N: both to review on one PR, all or nothing');
  git(path.join(A, 'tickets'), 'pull', '-q', '--rebase', 'origin', 'main');
  before = head();
  r = tool(A, ['done', 'T-1701', 'T-1703', '--pr', '901']);
  check('both in review on PR 901',
    r.status === 0 && front(remote('T-1701'), 'state') === 'review' && front(remote('T-1703'), 'state') === 'review'
    && front(remote('T-1701'), 'pr') === '901' && front(remote('T-1703'), 'pr') === '901', r.stdout + r.stderr);
  check('…in one commit naming both',
    git(root, '--git-dir', bare, 'rev-list', '--count', `${before}..main`).stdout.trim() === '1'
    && subject() === 'T-1701, T-1703: review — PR #901', subject());
  check('…and the group survives the rewrite', front(remote('T-1703'), 'group') === 'T-1701,T-1703');
  tool(A, ['claim', 'T-1721', 'T-1722']);
  before = head();
  r = tool(A, ['done', 'T-1721', 'T-1722', '--pr', '902']);
  check('a guard on one member (T-1722\'s image gate) refuses the whole group',
    r.status === 1 && /T-1722 IS NOT FINISHED/.test(r.stderr) && head() === before
    && front(remote('T-1721'), 'state') === 'claimed', r.stdout + r.stderr);
  r = tool(A, ['done', 'T-1721', 'T-1722', '--pr', '902', '--anyway', '--why', 'argued in the ticket']);
  check('…and --anyway passes them together', r.status === 0 && front(remote('T-1722'), 'state') === 'review', r.stderr);

  console.log('5. release: a claim the run will not finish goes back to open');
  git(path.join(B, 'tickets'), 'pull', '-q', '--rebase', 'origin', 'main');
  r = tool(B, ['release', 'T-1713', '--why', 'needs the bake this run is not doing'], runEnv(222));
  const rel = remote('T-1713');
  check('T-1713 is open, claim cleared, out of its group',
    r.status === 0 && front(rel, 'state') === 'open' && front(rel, 'claimed_by') === 'null'
    && front(rel, 'claimed_run') === 'null' && front(rel, 'claimed_at') === 'null' && front(rel, 'group') === undefined,
    r.stdout + r.stderr + rel);
  check('…the reason is written into its body', /\*\*Released \d{4}-\d{2}-\d{2}\*\* .*: needs the bake this run is not doing/.test(rel), rel);
  check('…it keeps its queue line', /^T-1713 — india$/m.test(git(root, '--git-dir', bare, 'show', 'main:QUEUE.md').stdout));
  check('…and its mate is a group no longer', front(remote('T-1711'), 'group') === undefined
    && front(remote('T-1711'), 'state') === 'claimed', remote('T-1711'));
  r = tool(B, ['release', 'T-1747']);
  check('release refuses a ticket that is not claimed', r.status === 1 && /T-1747 is open, not claimed/.test(r.stderr), r.stderr);
  r = tool(B, ['release', 'T-1701']);
  check('…and one in review, pointing at its PR', r.status === 1 && /in review on PR #901/.test(r.stderr), r.stderr);
  r = tool(B, ['release', 'T-1712'], runEnv(222));
  check('…and a live claim another run holds', r.status === 1 && /claimed by ANOTHER run/.test(r.stderr), r.stderr);

  console.log('6. the group field round-trips');
  git(path.join(A, 'tickets'), 'pull', '-q', '--rebase', 'origin', 'main');
  tool(A, ['board']);
  const json = JSON.parse(readFileSync(path.join(A, 'tickets', 'tickets.json'), 'utf8'));
  const jt = (id) => json.tickets.find((t) => t.id === id) ?? {};
  check('tickets.json carries it, and leaves it off a ticket never grouped',
    jt('T-1701').group === 'T-1701,T-1703' && jt('T-1721').group === 'T-1721,T-1722' && !('group' in jt('T-1747')),
    JSON.stringify([jt('T-1701'), jt('T-1747')]));
  check('a ticket never grouped carries no group line', !/^group:/m.test(remote('T-1747')) && !/^group:/m.test(remote('T-1712')));
  const board = readFileSync(path.join(A, 'tickets', 'BOARD.md'), 'utf8');
  check('BOARD.md says who ships with whom', /\*\*T-1701\*\*.*one PR with T-1703/.test(board), board.split('\n').filter((l) => /T-1701/.test(l)).join('\n'));

  console.log('7. a single id behaves exactly as before');
  r = tool(A, ['claim', 'T-1747']);
  check('claim T prints "T claimed", one commit named for it, no group line',
    r.status === 0 && r.stdout.trim().split('\n').pop() === 'T-1747 claimed'
    && /^T-1747: claim — run .* CT$/.test(subject()) && !/^group:/m.test(remote('T-1747')), r.stdout + subject());
  r = tool(A, ['claim', 'T-1702']);
  check('a refused single claim prints the reason alone and exits 1',
    r.status === 1 && /^T-1702 IS ALREADY CLAIMED/m.test(r.stderr) && !/NOT CLAIMED:/.test(r.stderr), r.stderr);
  r = tool(A, ['done', 'T-1747', '--pr', '903']);
  check('done T --pr N: review, its own message, no group line',
    r.status === 0 && /^T-1747 in review \(PR #903\)/.test(r.stdout) && subject() === 'T-1747: review — PR #903'
    && !/^group:/m.test(remote('T-1747')), r.stdout + subject());

  console.log('8. one house, one run: a group grows with --with, and nothing else gets on');
  r = tool(A, ['claim', 'T-1731', 'T-1732'], runEnv(333));
  check('a group on house 1801 is claimed together', r.status === 0 && front(remote('T-1732'), 'group') === 'T-1731,T-1732', r.stderr);
  r = tool(B, ['claim', 'T-1733'], runEnv(444));
  check('another run is refused Kimball (1801) while the group holds it', r.status === 1 && /work on house 1801/.test(r.stderr), r.stderr);
  r = tool(B, ['claim', 'T-1733'], runEnv(333));
  check('…and so is a claim merely sharing the run URL (slices of one workflow do)',
    r.status === 1 && /work on house 1801/.test(r.stderr), r.stderr);
  git(path.join(A, 'tickets'), 'pull', '-q', '--rebase', 'origin', 'main');
  r = tool(A, ['claim', 'T-1733', '--with', 'T-1731'], runEnv(333));
  check('the run holding the group adds it with --with T-1731',
    r.status === 0 && /joining T-1731's group/.test(subject()) && /one group, one PR: T-1731, T-1732, T-1733/.test(r.stdout),
    r.stdout + r.stderr);
  check('…and every member now reads the grown group',
    ['T-1731', 'T-1732', 'T-1733'].every((id) => front(remote(id), 'group') === 'T-1731,T-1732,T-1733'));
  r = tool(A, ['claim', 'T-1721', '--with', 'T-1747']);
  check('--with refuses a ticket this run does not hold', r.status === 1 && /--with T-1747: it is review/.test(r.stderr), r.stderr);

  console.log('9. list --workable --group: a shortlist of real links');
  r = tool(A, ['list', '--workable', '--group', 'T-1741']);
  const rowOf = (id) => (new RegExp(`^  ${id} .*\\n.*$`, 'm').exec(r.stdout) || [''])[0];
  check('offers the ticket sharing a file and the one naming the anchor, with effort',
    /T-1742  S .*\n.*shares navigator\.js/.test(rowOf('T-1742')) && /cross-referenced/.test(rowOf('T-1743')), r.stdout);
  check('…never an L, a pending decision, a live claim or a band-only neighbour',
    !/T-1744|T-1745|T-1746|T-1747/.test(r.stdout), r.stdout);
  check('…and says how to claim them together', /node tools\/ticket\.mjs claim T-1741 T-17\d\d/.test(r.stdout), r.stdout);

} finally {
  rmSync(root, { recursive: true, force: true });
}
console.log(failures ? `\ntest_ticket_group: ${failures} FAILED` : '\ntest_ticket_group: all hold');
process.exit(failures ? 1 : 0);
