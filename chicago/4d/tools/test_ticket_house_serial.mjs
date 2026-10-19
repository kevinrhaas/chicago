#!/usr/bin/env node
/**
 * test_ticket_house_serial.mjs — one run per house at a time (owner, 2026-10-19).
 *
 * Three slices held Glessner at once on 2026-10-19 (#1090, #1091, #1094): each rebaked
 * the house, each conflicted with the others' bakes, and their full smokes queued for
 * three hours and were cancelled. `claim` now refuses a ticket whose house already has
 * work in flight, and `list --workable` says so on the line. Run for real against a
 * tickets repository of its own, as test_ticket_repo_mode.mjs does:
 *
 *   1. a second claim on a claimed house is REFUSED, naming the holder, and the same
 *      house is matched by family name or number ("Glessner's" is 1800);
 *   2. another house, and a ticket outside the 1904 programme, are claimed freely;
 *   3. `list --workable` marks the busy house's open row HOUSE BUSY;
 *   4. a ticket in review and an open PR titled with a same-house ticket both hold it;
 *   5. an explicit `house:` holds a ticket outside the programme too;
 *   6. a DEAD claim holds nothing, and `--force` overrides.
 */
import { mkdtempSync, mkdirSync, rmSync, writeFileSync, cpSync, chmodSync } from 'node:fs';
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

const root = mkdtempSync(path.join(tmpdir(), 'c4d-house-'));
const bare = path.join(root, 'tickets.git');
const bin = path.join(root, 'bin');

function ticketText(id, title, extra = {}) {
  const fm = { id, title, state: 'open', epic: 'SOUTH_TIME', requested_by: 'owner', seen: false, effort: 'S',
    legacy_id: null, parent: null, opened: '2026-10-19', closed: null, pr: null, claimed_by: null,
    blocked_on: null, needs_bake: false, closed_at: null, claimed_run: null, ...extra };
  return `---\n${Object.entries(fm).map(([k, v]) => `${k}: ${v ?? 'null'}`).join('\n')}\n---\n\n${title}.\n\n**Acceptance:** it is done.\n`;
}

const TICKETS = [
  ['T-1601', "Glessner's north pairs' jambs read off HABS 13 and 14", {}],
  ['T-1602', "1800 Prairie's north stack's date stone", {}],
  ['T-1603', "Keith's loggia pairs ruled", {}],
  ['T-1604', "dev's still-frame ceiling broken on town_backyard", { epic: 'META' }],
  ['T-1605', "1637's south flank from the Grosvenor photograph", {}],
  ['T-1606', "1637 Prairie's bay columns", {}],
  ['T-1607', "1623's entrance porch", { state: 'review', pr: 880 }],
  ['T-1608', "1623's oriel at the drawing's size", {}],
  ['T-1609', 'A town-wide reading that happens to touch 1637', { epic: 'META', house: '1637' }],
  ['T-1610', "2100's front", { state: 'claimed', claimed_by: 'run 9/1/2026, 1:00:00 AM CT' }],
  ['T-1611', "2100 Prairie's rear", {}],
];

{
  const seed = path.join(root, 'seed');
  mkdirSync(path.join(seed, 'T-1500-1749'), { recursive: true });
  writeFileSync(path.join(seed, 'QUEUE.md'), `# QUEUE — top is next.\n\n${TICKETS.map(([id, t]) => `${id} — ${t}`).join('\n')}\n`);
  writeFileSync(path.join(seed, 'QUEUE_ORDER.md'), '# RE-RANK LEDGER\n#   2026-10-19  seeded\n');
  writeFileSync(path.join(seed, '.gitignore'), 'BOARD.md\ntickets.json\n');
  for (const [id, title, extra] of TICKETS) {
    writeFileSync(path.join(seed, 'T-1500-1749', `${id}-${id.slice(2)}.md`), ticketText(id, title, extra));
  }
  git(seed, 'init', '-q', '-b', 'main');
  git(seed, '-c', 'user.name=t', '-c', 'user.email=t@t', 'add', '-A');
  git(seed, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'seed');
  git(root, 'clone', '-q', '--bare', seed, bare);
}

// No network: `gh` and `curl` fail, so `claim` reads the open PRs only from --pr-json.
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
const env = { ...process.env, PATH: `${bin}:${process.env.PATH}`, GITHUB_ACTIONS: '', GITHUB_RUN_ID: '' };
delete env.CHICAGO_TICKETS_DIR;
const tool = (app, ...args) => spawnSync('node', [path.join(app, 'tools', 'ticket.mjs'), ...args],
  { cwd: app, encoding: 'utf8', env });

try {
  const A = sandbox('a');
  const B = sandbox('b');

  console.log('1. a claimed house refuses a second claim');
  let r = tool(A, 'claim', 'T-1601');
  check('run A claims T-1601 (Glessner)', r.status === 0, r.stderr);
  r = tool(B, 'claim', 'T-1602');
  check('run B is refused T-1602 (1800 Prairie, the same house), naming T-1601',
    r.status === 1 && /work on house 1800/.test(r.stderr) && /T-1601 claimed/.test(r.stderr), r.stdout + r.stderr);

  console.log('2. other houses and other work are free');
  r = tool(B, 'claim', 'T-1603');
  check('run B claims T-1603 (Keith, another house)', r.status === 0, r.stderr);
  r = tool(B, 'claim', 'T-1604');
  check('run B claims T-1604 (outside the 1904 programme, no house)', r.status === 0, r.stderr);

  console.log('3. list --workable shows the busy house');
  const listed = tool(B, 'list', '--workable').stdout;
  check('T-1602 reads HOUSE BUSY 1800 (T-1601)', /^T-1602  HOUSE BUSY 1800 \(T-1601\)/m.test(listed), listed);
  check('…and a free house\'s row reads open', /^T-1605  open /m.test(listed), listed);

  console.log('4. a review ticket and an open PR hold their house');
  r = tool(B, 'claim', 'T-1608');
  check('T-1608 is refused while T-1607 (1623) is in review with PR #880',
    r.status === 1 && /T-1607 in review, PR #880/.test(r.stderr), r.stdout + r.stderr);
  const pulls = path.join(root, 'pulls.json');
  writeFileSync(pulls, JSON.stringify([{ number: 900, title: "T-1605: 1637's south flank", state: 'open',
    merged_at: null, labels: ['resume'], head: { ref: 'steward/t1605-flank' } }]));
  r = tool(B, 'claim', 'T-1606', '--pr-json', pulls);
  check('T-1606 (1637) is refused while PR #900 titled T-1605 (1637) is open',
    r.status === 1 && /work on house 1637/.test(r.stderr) && /PR #900 on steward\/t1605-flank/.test(r.stderr), r.stdout + r.stderr);

  console.log('5. an explicit house: holds a ticket outside the programme');
  r = tool(B, 'claim', 'T-1609', '--pr-json', pulls);
  check('T-1609 (META, house: 1637) is refused for the same PR',
    r.status === 1 && /work on house 1637/.test(r.stderr), r.stdout + r.stderr);

  console.log('6. a dead claim holds nothing, and --force overrides');
  r = tool(B, 'claim', 'T-1611');
  check('T-1611 (2100) is claimed although T-1610 (2100) holds a claim weeks dead', r.status === 0, r.stdout + r.stderr);
  r = tool(B, 'claim', 'T-1602', '--force');
  check('--force claims a busy house', r.status === 0, r.stdout + r.stderr);
} finally {
  rmSync(root, { recursive: true, force: true });
}
console.log(failures ? `\ntest_ticket_house_serial: ${failures} FAILED` : '\ntest_ticket_house_serial: all hold');
process.exit(failures ? 1 : 0);
