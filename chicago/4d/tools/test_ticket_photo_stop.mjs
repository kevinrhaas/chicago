#!/usr/bin/env node
/**
 * test_ticket_photo_stop.mjs — THE PHOTO-TICKET STOPPING RULE (owner, 2026-10-25, T-3153).
 *
 * WHAT HAPPENED. Glessner took 115 tickets after the image gate opened on 2026-10-11,
 * fixed 110 picture differences and left 9, most under a foot or a few pixels; its
 * sign-off was re-filed five times (T-2228, T-2761, T-2854, T-3028, T-3117, T-3140).
 * Every closer look found a smaller gap, and a run filed it or split it. The owner:
 * "you need to help me with not creating more and more tickets when there are probably
 * some seriously diminishing returns", and he chose "Full rule, close 5 now".
 *
 *   1-3   `new` that is not the owner's is REFUSED for a photo-gated house (one with a
 *         reference view), before anything is written; `--anyway` cannot reach it
 *   4-5   …the owner's own filing still files, and so do a performance follow-up and one
 *         that blocks (dev's gate red on the house's derivative, as T-3004 was)
 *   6-7   a house with no reference view files under the cap and is refused at it
 *   8-9   `split` refuses a sign-off, and splits it when the owner asked, his words in
 *         every piece
 *   10-11 `split` refuses a gated house past the cap, and still splits one under it
 */
import { mkdtempSync, mkdirSync, rmSync, writeFileSync, readFileSync, readdirSync, cpSync } from 'node:fs';
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

const ticketText = (id, title, opened = '2026-10-20') => `---
id: ${id}
title: ${title}
state: open
epic: SOUTH_TIME
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: ${opened}
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

${title}.

**Acceptance:** fixture.
`;

const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-photo-stop-'));
const NO_PULLS = path.join(tmp, 'none.json');
writeFileSync(NO_PULLS, '[]');

/** An embedded-tickets sandbox: Glessner and Kimball are photo-gated, 1637 and 1621 are
 *  not; Glessner and 1637 each carry 25 tickets since the gate opened. */
function sandbox(name) {
  const root = path.join(tmp, name);
  const APP = path.join(root, 'chicago', '4d');
  mkdirSync(path.join(APP, 'tools'), { recursive: true });
  mkdirSync(path.join(APP, 'tickets'), { recursive: true });
  for (const d of ['glessner_house', 'kimball_house_1801_prairie']) mkdirSync(path.join(APP, 'data/reference_views', d), { recursive: true });
  cpSync(path.join(HERE, 'ticket.mjs'), path.join(APP, 'tools', 'ticket.mjs'));
  const rows = [];
  let n = 4000;
  const add = (title, opened) => {
    const id = `T-${n++}`;
    writeFileSync(path.join(APP, 'tickets', `${id}-fixture.md`), ticketText(id, title, opened));
    rows.push(`${id} — ${title}`);
    return id;
  };
  for (let i = 0; i < 24; i++) add(`Glessner's piece ${i}`);
  add("Glessner's piece from before the gate", '2026-10-01');   // not counted
  const signoff = add("Glessner's photographic sign-off: every match record reading matches");
  const eave = add("Glessner's north eave either side of the stable gable");
  for (let i = 0; i < 25; i++) add(`1637 Prairie's piece ${i}`);
  const kimball = add("1801 Prairie's south face from HABS photograph 1");
  const railing = add("1621 Prairie's stoop railing");
  writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'), `# QUEUE — top is next. THE OWNER ORDERS THIS FILE.\n\n${rows.join('\n')}\n`);
  git(root, 'init', '-q', '-b', 'dev');
  git(root, 'add', '-A');
  git(root, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'fixture');
  return { APP, signoff, eave, kimball, railing };
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

try {
  console.log('\n  a run filing a photo follow-up on a gated house');
  const A = sandbox('a');
  const before = files(A.APP).length;
  const loop = tool(A.APP, 'new', "Glessner's cornice reads 0.2 ft low in HABS 14 (found by T-4001)", '--by', 'loop', '--after', A.eave);
  check('1. a loop filing that names a photo-gated house is REFUSED',
    loop.status !== 0 && /REFUSED — house 1800 is photo-gated/.test(loop.out), loop.out.trim().split('\n')[0]);
  check('2. …it says where the gap goes instead, and nothing is written',
    /match record/.test(loop.out) && /within tolerance/.test(loop.out) && files(A.APP).length === before,
    `${before} file(s) before, ${files(A.APP).length} after`);
  const forced = tool(A.APP, 'new', "Glessner's cornice reads 0.2 ft low", '--by', 'loop', '--anyway', '--why', 'it matters');
  check('3. `--anyway` cannot take it — that is the budget\'s override, this is the owner\'s limit',
    forced.status !== 0 && /photo-gated/.test(forced.out) && files(A.APP).length === before, forced.out.trim().split('\n')[0]);
  const red = tool(A.APP, 'new', "Glessner's Light derivative is stale on dev", '--by', 'loop', '--after', A.eave, '--blocks', "dev's gate is red on it");
  check('   …but a filing that blocks (dev\'s gate red on the house) still files', red.status === 0, red.out.trim());
  const owner = tool(A.APP, 'new', "Glessner's porch lamp the owner reported", '--by', 'owner');
  check('4. the owner\'s own filing on that house still files', owner.status === 0 && files(A.APP).length === before + 2, owner.out.trim());
  const perf = tool(A.APP, 'new', "Glessner's close stand costs 40 ms a frame on the phone", '--by', 'loop');
  check('5. a performance follow-up is not photo work and still files', perf.status === 0, perf.out.trim());

  console.log('\n  a house with no reference view');
  const under = tool(A.APP, 'new', "1621 Prairie's gate latch", '--by', 'loop');
  check('6. under the cap, a loop filing still files', under.status === 0, under.out.trim());
  const at = tool(A.APP, 'new', "1637 Prairie's piece 26", '--by', 'loop');
  check('7. at the cap of 25 tickets since the gate, it is REFUSED',
    at.status !== 0 && /house 1637 has had 25 tickets/.test(at.out), at.out.trim().split('\n')[0]);

  console.log('\n  splitting');
  const B = sandbox('b');
  const s1 = tool(B.APP, 'split', B.signoff, 'first piece', 'second piece');
  check('8. a sign-off is never split', s1.status !== 0 && /is a sign-off/.test(s1.out) && stateOf(B.APP, B.signoff) === 'open', s1.out.trim().split('\n')[0]);
  const s2 = tool(B.APP, 'split', B.signoff, 'first piece', 'second piece', '--owner-asked', 'split the sign-off in two');
  const kid = files(B.APP).map((f) => readFileSync(path.join(B.APP, 'tickets', f), 'utf8')).find((t) => /^title: first piece$/m.test(t)) ?? '';
  check('9. …unless the owner asked, and every piece carries his words',
    s2.status === 0 && stateOf(B.APP, B.signoff) === 'split' && /> split the sign-off in two/.test(kid)
    && !files(B.APP).some((f) => /split-the-sign-off/.test(f)), s2.out.trim());
  const s3 = tool(B.APP, 'split', B.eave, 'first piece', 'second piece');
  check('10. a gated house past the cap is not split (Glessner here: 24 + this one + the sign-off)',
    s3.status !== 0 && /photo-gated and has had \d+ tickets/.test(s3.out), s3.out.trim().split('\n')[0]);
  const s4 = tool(B.APP, 'split', B.kimball, 'first piece', 'second piece');
  const s5 = tool(B.APP, 'split', B.railing, 'first piece', 'second piece');
  check('11. a gated house under the cap, and an ungated house, still split', s4.status === 0 && s5.status === 0, `${s4.out.trim()}\n${s5.out.trim()}`);
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
console.log(failures ? `\n  ${failures} FAILED` : '\n  all passed');
process.exit(failures ? 1 : 0);
