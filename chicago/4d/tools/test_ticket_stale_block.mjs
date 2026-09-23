#!/usr/bin/env node
/**
 * test_ticket_stale_block.mjs — `ticket.mjs check` refuses a ticket that is STILL
 * IN THE QUEUE while its `blocked_on` names a ticket that has finished.
 *
 * WHY THIS EXISTS (T-1142's run, 2026-09-15). T-0464 closed on 2026-09-14 as
 * #1257 — the ground reached Twenty-Second Street — and the three lines that lead
 * SOUTH THROUGH TIME, T-0465, T-0466 and T-0467, all went on reading
 *
 *     blocked_on: T-0464
 *
 * the next day. Nothing had to consume that field for it to do damage: a run
 * choosing work opens the top line, sees another ticket's id sitting in
 * `blocked_on`, and steps over it. The band's lead sat unclaimed while the line
 * below it was taken, and the owner is the one who noticed.
 *
 * THE SCOPE IS THE WHOLE POINT, so it is asserted rather than described. Measured
 * on dev the day this landed: 16 tickets named a finished blocker and only THREE
 * were workable. The other 13 sit on tickets that are themselves `done` or
 * `withdrawn`, where the field is honest history and nobody chooses work from it.
 * A guard that failed on those would be 13 lines of noise guarding nothing, and
 * the next person to meet it would weaken the whole check to shut it up — so the
 * check must stay silent about them, and that silence is a case below.
 *
 * The failure modes, each asserted:
 *   1. it does not fire at all — the fault ships;
 *   2. it fires on a DONE ticket's stale field — noise, and the check gets
 *      weakened later to quiet it;
 *   3. it fires on a LIVE block, where the blocker is genuinely unfinished —
 *      that is the field doing its job;
 *   4. it loses the blocker's state or its PR from the message, which is the
 *      receipt that says the dependency is satisfied rather than merely old.
 *
 * Everything runs in a sandbox, as test_ticket_after.mjs explains: the tool
 * resolves its paths from its own location, so a temporary tree beside a copy of
 * the tool is a whole world for it to be wrong in, and the real queue is untouched.
 */
import { mkdtempSync, mkdirSync, rmSync, cpSync, writeFileSync } from 'node:fs';
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

const ticketFile = ({ id, title, state = 'open', blocked_on = null, pr = null,
  closed = null, closed_at = null }) => `---
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
closed: ${closed ?? 'null'}
pr: ${pr ?? 'null'}
claimed_by: null
blocked_on: ${blocked_on ?? 'null'}
needs_bake: false
closed_at: ${closed_at ?? 'null'}
claimed_run: null
---

${title}.

**Acceptance:** fixture.
`;

/**
 * @param {object[]} tickets  frontmatter for each fixture ticket
 * @param {string[]} queued   the ids that appear as lines in QUEUE.md
 */
function sandbox(tickets, queued) {
  const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-stale-'));
  const APP = path.join(tmp, 'chicago', '4d');
  mkdirSync(path.join(APP, 'tools'), { recursive: true });
  mkdirSync(path.join(APP, 'tickets'), { recursive: true });
  cpSync(path.join(REPO, 'tools', 'ticket.mjs'), path.join(APP, 'tools', 'ticket.mjs'));
  for (const t of tickets) {
    writeFileSync(path.join(APP, 'tickets', `${t.id}-fixture.md`), ticketFile(t));
  }
  // The label has to be the ticket's own title: `check` asserts that the queue
  // line and the ticket agree, and a fixture that ignores it fails on THAT
  // instead — which would have this harness reporting red for a reason that has
  // nothing to do with the guard it exists to prove.
  const titleOf = (id) => tickets.find((t) => t.id === id).title;
  writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'),
    '# QUEUE — top is next. THE OWNER ORDERS THIS FILE.\n\n'
    + queued.map((id) => `${id} — ${titleOf(id)}`).join('\n') + '\n');
  return { tmp, APP };
}

const said = (e) => `${e.stdout ?? ''}${e.stderr ?? ''}`;
function runCheck(APP) {
  try {
    return { ok: true, out: execFileSync('node', [path.join(APP, 'tools', 'ticket.mjs'), 'check'],
      { cwd: APP, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }) };
  } catch (e) { return { ok: false, out: said(e) }; }
}

/** The blocker, finished, exactly as T-0464 was. */
const DONE_BLOCKER = {
  id: 'T-0001', title: 'The ground reaches Twenty-Second Street', state: 'done',
  pr: 1257, closed: '2026-09-14', closed_at: '2026-09-14T12:00:00.000Z',
};
/** The blocker, unfinished. */
const OPEN_BLOCKER = { id: 'T-0001', title: 'The ground reaches Twenty-Second Street' };

console.log('\n\x1b[1m== a queue line blocked on a ticket that has finished\x1b[0m');

/* ------------------------------------- 1 & 4: it fires, and it names the receipt */
{
  const { tmp, APP } = sandbox([
    DONE_BLOCKER,
    { id: 'T-0002', title: 'Trace the South Branch through the expanded field', blocked_on: 'T-0001' },
  ], ['T-0002']);
  try {
    const r = runCheck(APP);
    check('the check FAILS', !r.ok, r.ok ? 'it passed — the fault would ship' : undefined);
    check('it names the ticket that is wrong', /T-0002/.test(r.out));
    check('it names the blocker AND that the blocker is done',
      /T-0001/.test(r.out) && /done/.test(r.out));
    check('it carries the blocker\'s PR, which is the receipt',
      /#1257/.test(r.out), r.out.split('\n').find((l) => /T-0002/.test(l))?.trim());
    check('it says the dependency is satisfied rather than merely old',
      /SATISFIED/i.test(r.out));
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* ----------------------------------------- 2: silent about a FINISHED ticket's field */
{
  const { tmp, APP } = sandbox([
    DONE_BLOCKER,
    // Done, and still naming its old blocker — 13 of dev's tickets look like this.
    { id: 'T-0002', title: 'A ticket that finished long ago', state: 'done',
      blocked_on: 'T-0001', pr: 668, closed: '2026-09-02',
      closed_at: '2026-09-02T12:00:00.000Z' },
    { id: 'T-0003', title: 'Something still to do' },
  ], ['T-0003']);
  try {
    const r = runCheck(APP);
    check('a DONE ticket\'s stale blocked_on is history, and passes',
      r.ok, r.ok ? undefined : r.out.trim());
    check('…and it is not merely unmentioned in a failing run: nothing fires at all',
      r.ok && !/T-0002/.test(r.out), r.out.trim().split('\n').slice(0, 2).join(' / '));
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* ------------------------------------------------ 3: a LIVE block is the field working */
{
  const { tmp, APP } = sandbox([
    OPEN_BLOCKER,
    { id: 'T-0002', title: 'Waits on the ground, which is genuinely unfinished', blocked_on: 'T-0001' },
  ], ['T-0001', 'T-0002']);
  try {
    const r = runCheck(APP);
    check('a queue line blocked on an OPEN ticket passes — that is the field doing its job',
      r.ok, r.ok ? undefined : r.out.trim());
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* --------------------------------- and a blocked_on that is prose, not an id, is left alone */
{
  const { tmp, APP } = sandbox([
    { id: 'T-0002', title: 'Waiting on a decision only the owner can make',
      state: 'blocked-owner', blocked_on: 'Which of the two shorelines does the scene take?' },
    { id: 'T-0003', title: 'Something still to do' },
  ], ['T-0003']);
  try {
    const r = runCheck(APP);
    check('a blocked_on holding a QUESTION rather than an id is untouched',
      r.ok, r.ok ? undefined : r.out.trim());
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

console.log(`\n${failures ? `\x1b[31m${failures} check(s) FAILED\x1b[0m`
  : '\x1b[32mstale-block guard OK — it fires on a live queue line and stays quiet elsewhere\x1b[0m'}`);
process.exit(failures ? 1 : 0);
