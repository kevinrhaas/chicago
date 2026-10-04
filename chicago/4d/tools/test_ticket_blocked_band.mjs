#!/usr/bin/env node
/**
 * test_ticket_blocked_band.mjs — band 8b's commented `# BLOCKED-* T-NNNN` lines are
 * written by `ticket.mjs block`, taken out by every verb that unblocks, and refused
 * by `check` when one ticket stands there twice.
 *
 * WHY THIS EXISTS (T-1541). T-1518 gave blocked tickets a band and a gate that
 * refuses a blocked ticket named nowhere in QUEUE.md — but `block` itself only
 * removed the queue line and wrote nothing in its place. The line the gate demands
 * was therefore written by hand, and both ways that goes wrong happened:
 *
 *   - T-1479 stood in no band at all until a run's gate caught it;
 *   - T-1532 and T-1536 each stood TWICE in band 8b, because two branches each
 *     hand-wrote the same block, and the queue's duplicate check reads only
 *     uncommented lines, so nothing saw it.
 *
 * The failure modes, each asserted:
 *   1. `block` leaves the ticket in no band — the gate goes red on the tool's own
 *      output, and the next person hand-writes the line again;
 *   2. blocking twice (or owner → tech) adds a second line instead of replacing;
 *   3. `unblock` / `withdraw` leave the 8b line behind — the band then describes a
 *      queue that has moved on, and `check` is red on that instead;
 *   4. `check` is silent about a band line standing twice — the T-1532 shape;
 *   5. the line lands outside band 8b, or with no band to land in it is lost.
 *
 * Everything runs in a sandbox, as test_ticket_after.mjs explains: the tool
 * resolves its paths from its own location, so a temporary tree beside a copy of
 * the tool is a whole world for it to be wrong in, and the real queue is untouched.
 */
import { mkdtempSync, mkdirSync, rmSync, cpSync, writeFileSync, readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const REPO = path.resolve(HERE, '..');

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

/* ------------------------------------------------------------------ fixture */

const LONG = 'The crews of the vessels in port and the harbour-works gang seated, once a '
  + 'committed source gives a schooner her complement and the harbour report is read';
const TICKETS = [
  { id: 'T-0001', title: 'Something still to do' },
  { id: 'T-0002', title: 'Waits on a source nobody has committed' },
  { id: 'T-0003', title: LONG },
];

const ticketFile = ({ id, title, state = 'open' }) => `---
id: ${id}
title: ${title}
state: ${state}
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-01
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

/** @param {string} tail  what follows the queue lines — the bands, or nothing */
function sandbox(tail) {
  const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-band8b-'));
  const APP = path.join(tmp, 'chicago', '4d');
  mkdirSync(path.join(APP, 'tools'), { recursive: true });
  mkdirSync(path.join(APP, 'tickets'), { recursive: true });
  cpSync(path.join(REPO, 'tools', 'ticket.mjs'), path.join(APP, 'tools', 'ticket.mjs'));
  for (const t of TICKETS) writeFileSync(path.join(APP, 'tickets', `${t.id}-fixture.md`), ticketFile(t));
  writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'),
    '# QUEUE — top is next. THE OWNER ORDERS THIS FILE.\n\n'
    + TICKETS.map((t) => `${t.id} — ${t.title}`).join('\n') + '\n' + tail);
  return { tmp, APP, queue: () => readFileSync(path.join(APP, 'tickets', 'QUEUE.md'), 'utf8') };
}

const said = (e) => `${e.stdout ?? ''}${e.stderr ?? ''}`;
function run(APP, ...args) {
  try {
    return { ok: true, out: execFileSync('node', [path.join(APP, 'tools', 'ticket.mjs'), ...args],
      { cwd: APP, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }) };
  } catch (e) { return { ok: false, out: said(e) }; }
}
const bandLines = (q, id) => q.split('\n').filter((l) => new RegExp(`^#\\s*BLOCKED-(?:OWNER|TECH)\\s+${id}\\b`).test(l));
/** The lines strictly between band 8b's heading and the next band heading. */
function band8b(q) {
  const lines = q.split('\n');
  const head = lines.findIndex((l) => /^# --- 8b\./.test(l));
  if (head < 0) return null;
  let end = lines.findIndex((l, i) => i > head && /^# --- /.test(l));
  if (end < 0) end = lines.length;
  return lines.slice(head + 1, end);
}

const BANDS = '\n# --- 8b. BLOCKED AND WAITING\n#\n# prose about the band\n#\n# --- 9. LOOP IMPROVEMENTS\n';

console.log('\n\x1b[1m== band 8b is written by the tool, once\x1b[0m');

/* ------------------------------------------- 1 & 5: block writes the line, inside 8b */
{
  const { tmp, APP, queue } = sandbox(BANDS);
  try {
    const b = run(APP, 'block', 'T-0002', '--on', 'a committed source for the complement');
    check('`block` runs', b.ok, b.ok ? undefined : b.out.trim());
    const q = queue();
    check('the ticket leaves the workable queue', !/^T-0002\b/m.test(q));
    check('…and is named in band 8b, as BLOCKED-TECH', bandLines(q, 'T-0002').length === 1
      && /BLOCKED-TECH T-0002 \(opened 2026-09-01, META\) — Waits on a source/.test(q),
    bandLines(q, 'T-0002')[0]);
    const inBand = band8b(q) ?? [];
    check('the line sits INSIDE band 8b, above band 9',
      inBand.some((l) => /T-0002/.test(l)), inBand.join(' / '));
    check('its `blocked_on` travels with it as the `waits:` line',
      inBand.some((l) => /^#\s{3,}waits: a committed source for the complement$/.test(l)));
    const c = run(APP, 'check');
    check('`check` is green on what `block` wrote', c.ok, c.ok ? undefined : c.out.trim());

    /* -------------------------------- 2: re-blocking replaces, never adds */
    run(APP, 'block', 'T-0002', '--owner', '--on', 'which source does the owner accept?');
    const q2 = queue();
    check('blocking again leaves ONE line for the ticket', bandLines(q2, 'T-0002').length === 1,
      bandLines(q2, 'T-0002').join(' / '));
    check('…and it is the new kind, with the new reason',
      /BLOCKED-OWNER T-0002/.test(q2) && /waits: which source does the owner accept\?/.test(q2)
      && !/a committed source for the complement/.test(q2));

    /* ------------------------------------- a long title is cut, not wrapped */
    run(APP, 'block', 'T-0003', '--on', 'T-0001');
    const long = bandLines(queue(), 'T-0003')[0] ?? '';
    check('a long title is cut with an ellipsis on one line', /…$/.test(long) && long.length < 200,
      `${long.length} chars`);
    const c2 = run(APP, 'check');
    check('`check` is green with two tickets in the band', c2.ok, c2.ok ? undefined : c2.out.trim());

    /* ------------------------------ 3: unblock and withdraw take the line out */
    run(APP, 'unblock', 'T-0002');
    const q3 = queue();
    check('`unblock` takes the 8b line out', bandLines(q3, 'T-0002').length === 0
      && !/waits: which source/.test(q3));
    check('…and puts the ticket back in the workable queue', /^T-0002\b/m.test(q3));
    run(APP, 'withdraw', 'T-0003', '--why', 'its work landed elsewhere');
    const q4 = queue();
    check('`withdraw` takes the 8b line out', bandLines(q4, 'T-0003').length === 0
      && !/waits: T-0001/.test(q4));
    const c3 = run(APP, 'check');
    check('`check` is green after both', c3.ok, c3.ok ? undefined : c3.out.trim());
    check('…and the band heading and band 9 survive the round trip',
      /^# --- 8b\./m.test(q4) && /^# --- 9\./m.test(q4));
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* --------------------------------------------- 5: no band at all, the line still lands */
{
  const { tmp, APP, queue } = sandbox('');
  try {
    run(APP, 'block', 'T-0002', '--on', 'a source');
    const q = queue();
    check('with no band 8b, `block` writes the heading and the line under it',
      (band8b(q) ?? []).some((l) => /BLOCKED-TECH T-0002/.test(l)), q.split('\n').slice(-3).join(' / '));
    const c = run(APP, 'check');
    check('`check` is green on it', c.ok, c.ok ? undefined : c.out.trim());
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* ---------------------------------------------- 4: check refuses the T-1532 shape */
{
  const { tmp, APP } = sandbox(BANDS);
  try {
    run(APP, 'block', 'T-0002', '--on', 'a source');
    // The merge artefact, by hand: a second branch's copy of the same block.
    const qp = path.join(APP, 'tickets', 'QUEUE.md');
    const q = readFileSync(qp, 'utf8');
    const line = bandLines(q, 'T-0002')[0];
    writeFileSync(qp, q.replace(line, `${line}\n${line}`));
    const c = run(APP, 'check');
    check('the check FAILS on a band line standing twice', !c.ok, c.ok ? 'it passed — the fault would ship' : undefined);
    check('…naming the ticket and saying twice', /band 8b lists T-0002 twice/.test(c.out),
      c.out.split('\n').find((l) => /T-0002/.test(l))?.trim());
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

console.log(`\n${failures ? `\x1b[31m${failures} check(s) FAILED\x1b[0m`
  : '\x1b[32mband 8b OK — block writes its line once, unblock and withdraw take it out, check refuses a twice\x1b[0m'}`);
process.exit(failures ? 1 : 0);
