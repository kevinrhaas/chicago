#!/usr/bin/env node
/**
 * test_ticket_split_gate.mjs — A SPLIT PARENT'S IMAGE GATE IS CLOSED BY ITS LAST PIECE.
 *
 * WHAT HAPPENED. On 1729 Prairie, T-1881 (the Pullman house, with an `## Image gate`
 * section) was split into five pieces and T-1934 (the stable and conservatory) into seven.
 * `split` closes the parent without asking the gate, and its pieces carried no gate section,
 * so every piece closed and the house's match records still said `differs`. The owner,
 * 2026-10-28: "it is still way off from a photographic match ... did you consider it done?"
 *
 *   1   a piece whose sibling is still open closes on its own slice, as before
 *   2   the LAST open piece is refused while the parent's building does not match
 *   3   …and closes once it does
 *   4   two last pieces closed together are refused
 *   5   a sibling in `review` already passed its own `done`, so the other is the last piece
 *   6   the gate of a split grandparent is asked too
 *   7   `split` writes into every piece that the gate stays on the parent
 *
 * The sandbox's image_gate.mjs is a stub: red while a GATE_RED file stands beside it.
 */
import { mkdtempSync, mkdirSync, rmSync, writeFileSync, readFileSync, readdirSync, cpSync, existsSync } from 'node:fs';
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

const GATE = '\n## Image gate (owner, 2026-10-11, T-2368)\n\nPictures: fixture.\n\n- test_house_1729\n';
const ticketText = (id, title, { state = 'open', parent = null, gate = false } = {}) => `---
id: ${id}
title: ${title}
state: ${state}
epic: SOUTH_TIME
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: ${parent}
opened: 2026-10-20
closed: ${state === 'split' ? '2026-10-25' : 'null'}
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

${title}.

**Acceptance:** fixture.
${gate ? GATE : ''}`;

const STUB = `import { existsSync } from 'node:fs';
import path from 'node:path';
const here = path.dirname(new URL(import.meta.url).pathname);
if (existsSync(path.join(here, 'GATE_RED'))) { console.log('test_house_1729: view a differs'); process.exit(1); }
console.log('test_house_1729: every view matches');
`;

const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-split-gate-'));
const NO_PULLS = path.join(tmp, 'none.json');
writeFileSync(NO_PULLS, '[]');

/** T-5000 (gated, split) -> T-5001, T-5002; T-5010 (gated, split) -> T-5011 (split) -> T-5012,
 *  T-5013; T-5020 gated and open, to be split. */
function sandbox(name, { red = true, states = {} } = {}) {
  const root = path.join(tmp, name);
  const APP = path.join(root, 'chicago', '4d');
  mkdirSync(path.join(APP, 'tools'), { recursive: true });
  mkdirSync(path.join(APP, 'tickets'), { recursive: true });
  cpSync(path.join(HERE, 'ticket.mjs'), path.join(APP, 'tools', 'ticket.mjs'));
  writeFileSync(path.join(APP, 'tools', 'image_gate.mjs'), STUB);
  if (red) writeFileSync(path.join(APP, 'tools', 'GATE_RED'), '');
  const rows = [];
  const add = (id, title, opts = {}) => {
    const state = states[id] ?? opts.state ?? 'open';
    writeFileSync(path.join(APP, 'tickets', `${id}-fixture.md`), ticketText(id, title, { ...opts, state }));
    if (['open', 'claimed', 'review'].includes(state)) rows.push(`${id} — ${title}`);
  };
  add('T-5000', "1729 Prairie's house finished", { state: 'split', gate: true });
  add('T-5001', "1729 Prairie's portico", { parent: 'T-5000' });
  add('T-5002', "1729 Prairie's dormers", { parent: 'T-5000' });
  add('T-5010', "1729 Prairie's stable finished", { state: 'split', gate: true });
  add('T-5011', "1729 Prairie's stable roof", { state: 'split', parent: 'T-5010' });
  add('T-5012', "1729 Prairie's stable belvedere", { parent: 'T-5011' });
  add('T-5013', "1729 Prairie's stable arcade", { parent: 'T-5011' });
  add('T-5020', "1729 Prairie's glasshouses finished", { gate: true });
  writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'), `# QUEUE — top is next. THE OWNER ORDERS THIS FILE.\n\n${rows.join('\n')}\n`);
  git(root, 'init', '-q', '-b', 'dev');
  git(root, 'add', '-A');
  git(root, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'fixture');
  return APP;
}
const env = { ...process.env, GITHUB_ACTIONS: '', GITHUB_RUN_ID: '' };
delete env.CHICAGO_TICKETS_DIR;
const tool = (APP, ...args) => {
  if (args[0] === 'split') args = [...args, '--pr-json', NO_PULLS];
  const r = spawnSync('node', [path.join(APP, 'tools', 'ticket.mjs'), ...args], { cwd: APP, encoding: 'utf8', env });
  return { status: r.status, out: `${r.stdout ?? ''}${r.stderr ?? ''}` };
};
const files = (APP) => readdirSync(path.join(APP, 'tickets')).filter((f) => /^T-\d+.*\.md$/.test(f));
const stateOf = (APP, id) => /^state: (\S+)/m.exec(readFileSync(path.join(APP, 'tickets', files(APP).find((f) => f.startsWith(id))), 'utf8'))?.[1];
const INHERITED = /LAST OPEN PIECE OF T-5000/;

try {
  console.log('\n  the pieces of a split, gated house');
  const A = sandbox('a');
  const first = tool(A, 'done', 'T-5001', '--pr', '1');
  check('1. a piece whose sibling is still open closes on its own slice', first.status === 0 && stateOf(A, 'T-5001') === 'done', first.out.trim());
  const last = tool(A, 'done', 'T-5002', '--pr', '2');
  check('2. the last open piece is REFUSED while the parent\'s building does not match',
    last.status !== 0 && INHERITED.test(last.out) && /view a differs/.test(last.out) && stateOf(A, 'T-5002') === 'open',
    last.out.trim().split('\n').slice(0, 3).join(' | '));

  const B = sandbox('b', { red: false, states: { 'T-5001': 'done' } });
  const green = tool(B, 'done', 'T-5002', '--pr', '2');
  check('3. …and closes once every view matches', green.status === 0 && stateOf(B, 'T-5002') === 'done', green.out.trim());

  const C = sandbox('c');
  const both = tool(C, 'done', 'T-5001', 'T-5002', '--pr', '3');
  check('4. two last pieces closed together are refused', both.status !== 0 && INHERITED.test(both.out)
    && stateOf(C, 'T-5001') === 'open' && stateOf(C, 'T-5002') === 'open', both.out.trim().split('\n')[0]);

  const D = sandbox('d', { states: { 'T-5001': 'review' } });
  const afterReview = tool(D, 'done', 'T-5002', '--pr', '4');
  check('5. a sibling in review already passed its own done, so this is the last piece',
    afterReview.status !== 0 && INHERITED.test(afterReview.out), afterReview.out.trim().split('\n')[0]);

  const E = sandbox('e', { states: { 'T-5012': 'done' } });
  const grand = tool(E, 'done', 'T-5013', '--pr', '5');
  check('6. the gate of a split grandparent is asked by its last grandchild',
    grand.status !== 0 && /LAST OPEN PIECE OF T-5010/.test(grand.out), grand.out.trim().split('\n')[0]);

  console.log('\n  splitting a gated ticket');
  const F = sandbox('f');
  const s = tool(F, 'split', 'T-5020', 'first piece', 'second piece');
  const kids = files(F).map((f) => readFileSync(path.join(F, 'tickets', f), 'utf8')).filter((t) => /^parent: T-5020$/m.test(t));
  check('7. every piece says the gate stays on the parent and its last piece closes it',
    s.status === 0 && kids.length === 2 && kids.every((t) => /## Image gate stays on T-5020/.test(t) && !/^## Image gate \(/m.test(t)),
    s.out.trim());
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
console.log(failures ? `\n  ${failures} FAILED` : '\n  all passed');
process.exit(failures ? 1 : 0);
