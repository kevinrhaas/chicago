#!/usr/bin/env node
/**
 * test_ticket_after.mjs — `new --after T-NNNN` places the new line DIRECTLY UNDER
 * the ticket it names, wherever that ticket sits, and touches no other line.
 *
 * WHY THIS EXISTS (owner, 2026-09-10). Every run filed what it found at the foot
 * of QUEUE.md, so by 2026-09-10 the file was 195 lines and its bottom third was
 * findings filed under the ticket that found them and never worked — "I don't want
 * you to keep adding a whole bunch of tickets below your current one". `--after`
 * is the remedy: a run's filing goes beside the work it serves, inside that band.
 *
 * The failure modes a placement flag can have, and each is asserted here:
 *   1. it lands at a fixed INDEX rather than under the named ticket — so the same
 *      call is run against two orderings of one fixture, and the line must follow
 *      the anchor both times;
 *   2. it moves or relabels the ANCHOR or its neighbours — every pre-existing line
 *      must be byte-identical afterwards, in its original order;
 *   3. it falls back SILENTLY when the anchor is not in the queue — the fallback is
 *      allowed (append), but the tool must say so, or the run believes it chose;
 *   4. the anchor id leaks into the TITLE — `new` builds the title from every
 *      non-flag argument, so `--after`'s value has to be excluded from it;
 *   5. a bare number is accepted for the anchor (`--after 2` is T-0002), because
 *      that is how every other id argument in this tool reads.
 *
 * EVERYTHING RUNS IN A SANDBOX, as test_ticket_restamp.mjs explains: the tool
 * resolves its paths from its own location, so a temporary tree beside a copy of
 * the tool is a whole world for it to be wrong in, and the real queue is never
 * touched.
 */
import { mkdtempSync, mkdirSync, rmSync, cpSync, readFileSync, writeFileSync } from 'node:fs';
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

const ticketFile = (id, title) => `---
id: ${id}
title: ${title}
state: open
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-10
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

const A = ['T-0001', 'The first ticket the owner ranked'];
const B = ['T-0002', 'The ticket a run is working, and files beside'];
const C = ['T-0003', 'The third ticket the owner ranked'];

function sandbox(order) {
  const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-after-'));
  const APP = path.join(tmp, 'chicago', '4d');
  mkdirSync(path.join(APP, 'tools'), { recursive: true });
  mkdirSync(path.join(APP, 'tickets'), { recursive: true });
  cpSync(path.join(REPO, 'tools', 'ticket.mjs'), path.join(APP, 'tools', 'ticket.mjs'));
  for (const [id, title] of [A, B, C]) {
    writeFileSync(path.join(APP, 'tickets', `${id}-fixture.md`), ticketFile(id, title));
  }
  // A band comment between two lines, so "byte-identical afterwards" covers the
  // prose the owner writes as well as the ticket lines.
  const lines = order.map(([id, title]) => `${id} — ${title}`);
  lines.splice(1, 0, '# --- a band the owner wrote, which must survive untouched');
  writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'),
    '# QUEUE — top is next. THE OWNER ORDERS THIS FILE.\n\n' + lines.join('\n') + '\n');
  return { tmp, APP };
}

const RUN = (APP) => ({ cwd: APP, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
const said = (e) => `${e.stdout ?? ''}${e.stderr ?? ''}`;
const tool = (APP, ...args) => execFileSync('node',
  [path.join(APP, 'tools', 'ticket.mjs'), ...args], RUN(APP));
const queueText = (APP) => readFileSync(path.join(APP, 'tickets', 'QUEUE.md'), 'utf8');
const rows = (APP) => queueText(APP).split('\n').filter((l) => l.trim() !== '');
const idOfRow = (l) => /^(T-\d{4})\b/.exec(l.trim())?.[1] ?? null;
function checkTool(APP) {
  try { return { ok: true, out: tool(APP, 'check') }; } catch (e) { return { ok: false, out: said(e) }; }
}

/* ------------------------------------- 1 & 2: follows the anchor, moves nothing */

function placeWith(label, order) {
  const { tmp, APP } = sandbox(order);
  try {
    console.log(`\n  ${label}`);
    const before = rows(APP);
    const out = tool(APP, 'new', 'A finding filed beside the work', '--after', 'T-0002', '--by', 'loop');
    const newId = /^(T-\d{4}) created/m.exec(out)?.[1];
    check('a ticket is created', /^T-\d{4}$/.test(newId ?? ''), out.trim().split('\n')[0]);
    check('the message says where it went, and that it was placed',
      /placed directly under T-0002/.test(out), out.trim());

    const after = rows(APP);
    const anchorAt = after.findIndex((l) => idOfRow(l) === 'T-0002');
    const newAt = after.findIndex((l) => idOfRow(l) === newId);
    check('the new line sits DIRECTLY UNDER the anchor, wherever the anchor is',
      newAt === anchorAt + 1, `anchor row ${anchorAt}, new row ${newAt}`);

    const withoutNew = after.filter((l) => idOfRow(l) !== newId);
    check('every pre-existing line is byte-identical and in its original order',
      withoutNew.length === before.length && withoutNew.every((l, i) => l === before[i]),
      withoutNew.length === before.length ? undefined : `${before.length} → ${withoutNew.length} lines`);

    const title = /^title: (.*)$/m.exec(readFileSync(
      path.join(APP, 'tickets', `${newId}-a-finding-filed-beside-the-work.md`), 'utf8'))?.[1];
    check('the anchor id did not leak into the title', title === 'A finding filed beside the work', title);

    const c = checkTool(APP);
    check('and `check` is green afterwards, with nothing repaired by hand', c.ok, c.out.trim().split('\n').pop());
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

placeWith('the anchor is the middle line', [A, B, C]);
placeWith('the same call with the lines reordered — the anchor is now the LAST line', [C, A, B]);

/* ------------------------------------------------ 3: the fallback is not silent */

{
  const { tmp, APP } = sandbox([A, B, C]);
  try {
    console.log('\n  the anchor is not in the queue');
    const before = rows(APP);
    const out = tool(APP, 'new', 'A finding whose anchor has closed', '--after', 'T-0099', '--by', 'loop');
    const newId = /^(T-\d{4}) created/m.exec(out)?.[1];
    const after = rows(APP);
    check('the line is appended at the bottom rather than dropped',
      idOfRow(after[after.length - 1]) === newId && after.length === before.length + 1);
    check('and the tool SAYS the anchor was not found — a fallback is never mistaken for a choice',
      /T-0099 is not in QUEUE/.test(out) && /appended to the bottom/.test(out), out.trim());
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* --------------------------------------------------- 5: a bare number is an id */

{
  const { tmp, APP } = sandbox([A, B, C]);
  try {
    console.log('\n  the anchor given as a bare number');
    const out = tool(APP, 'new', 'A finding filed by number', '--after', '2', '--by', 'loop');
    const newId = /^(T-\d{4}) created/m.exec(out)?.[1];
    const after = rows(APP);
    const anchorAt = after.findIndex((l) => idOfRow(l) === 'T-0002');
    check('`--after 2` reads as T-0002 and places under it',
      after.findIndex((l) => idOfRow(l) === newId) === anchorAt + 1, out.trim().split('\n')[0]);
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* ----------------------------------------------------- 6: no --after still works */

{
  const { tmp, APP } = sandbox([A, B, C]);
  try {
    console.log('\n  no --after at all — the owner\'s own filing');
    const out = tool(APP, 'new', 'An owner filing', '--by', 'owner');
    const after = rows(APP);
    const newId = /^(T-\d{4}) created/m.exec(out)?.[1];
    check('appends to the bottom as before', idOfRow(after[after.length - 1]) === newId);
    check('and the message tells a run what it should have passed',
      /appended to QUEUE bottom/.test(out) && /--after/.test(out), out.trim());
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* ------------------------- 7-12: a follow-up that is not the owner's goes to band 9 */
// Owner, 2026-09-27: "move loop follow-ups to band 9", then "make the ticket tool enforce
// it". The queue below has a build band, band 9 and band 10, which is the shape the rule
// reads; the fixtures above have no band 9 and are the proof that nothing changes there.

const D = ['T-0004', 'A loop improvement already waiting in band 9'];
const E = ['T-0005', 'A research reading in band 10'];

function banded() {
  const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-band9-'));
  const APP = path.join(tmp, 'chicago', '4d');
  mkdirSync(path.join(APP, 'tools'), { recursive: true });
  mkdirSync(path.join(APP, 'tickets'), { recursive: true });
  cpSync(path.join(REPO, 'tools', 'ticket.mjs'), path.join(APP, 'tools', 'ticket.mjs'));
  for (const [id, title] of [A, B, C, D, E]) {
    writeFileSync(path.join(APP, 'tickets', `${id}-fixture.md`), ticketFile(id, title));
  }
  writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'), [
    '# QUEUE — top is next. THE OWNER ORDERS THIS FILE.', '',
    '# --- 5C. STRUCTURES — build', `${A[0]} — ${A[1]}`, `${B[0]} — ${B[1]}`, `${C[0]} — ${C[1]}`, '',
    '# --- 9. LOOP IMPROVEMENTS', `${D[0]} — ${D[1]}`, '',
    '# --- 10. RESEARCH COMPLETION', `${E[0]} — ${E[1]}`, ''].join('\n'));
  return { tmp, APP };
}
const band9Ids = (APP) => {
  const all = queueText(APP).split('\n');
  const h = all.findIndex((l) => l.startsWith('# --- 9.'));
  const e = all.findIndex((l) => l.startsWith('# --- 10.'));
  return all.slice(h, e).map(idOfRow).filter(Boolean);
};
function filed(label, args, expect) {
  const { tmp, APP } = banded();
  try {
    console.log(`\n  ${label}`);
    const before = rows(APP);
    let out;
    try { out = tool(APP, 'new', ...args); } catch (e) { out = said(e); if (expect.refused) { expect.refused(out); return; } throw e; }
    const newId = /^(T-\d{4}) created/m.exec(out)?.[1];
    const after = rows(APP);
    expect.check(APP, newId, after, out);
    const withoutNew = after.filter((l) => idOfRow(l) !== newId);
    check('every pre-existing line is byte-identical and in its original order',
      withoutNew.length === before.length && withoutNew.every((l, i) => l === before[i]));
    const c = checkTool(APP);
    check('and `check` is green afterwards', c.ok, c.out.trim().split('\n').pop());
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

filed('a loop follow-up --after a 5C build ticket', ['A tooling fault found mid-build', '--after', 'T-0002', '--by', 'loop'], {
  check(APP, id, after, out) {
    const b9 = band9Ids(APP);
    check('it lands at the FOOT of band 9, not under the build', b9[b9.length - 1] === id, b9.join(' '));
    check('and not under the anchor', after[after.findIndex((l) => idOfRow(l) === 'T-0002') + 1] !== after.find((l) => idOfRow(l) === id));
    check('the message says so, names the anchor it declined and the way past it',
      /FOOT OF BAND 9/.test(out) && /T-0002 sits above band 9/.test(out) && /--blocks/.test(out), out.trim());
  } });

filed('a steward filing with no --by and no --after', ['A finding with nowhere to stand'], {
  check(APP, id) { const b9 = band9Ids(APP); check('the default filer is not the owner, so it goes to band 9 too', b9[b9.length - 1] === id, b9.join(' ')); } });

filed('the same follow-up with --blocks and its reason', ['A fault the build cannot finish without', '--after', 'T-0002', '--by', 'loop', '--blocks', 'T-0002 cannot bake until this is fixed'], {
  check(APP, id, after, out) {
    const at = after.findIndex((l) => idOfRow(l) === 'T-0002');
    check('--blocks honours the anchor: it sits directly under T-0002', idOfRow(after[at + 1]) === id, out.trim());
    const body = readFileSync(path.join(APP, 'tickets', `${id}-a-fault-the-build-cannot-finish-without.md`), 'utf8');
    check('the reason is written into the ticket', /FILED ABOVE BAND 9, BECAUSE IT BLOCKS/.test(body) && /T-0002 cannot bake until this is fixed/.test(body));
    check('and the reason did not leak into the title', /^title: A fault the build cannot finish without$/m.test(body));
  } });

filed('an owner filing --after a 5C build ticket', ['Something the owner asked for', '--after', 'T-0002', '--by', 'owner'], {
  check(APP, id, after) { const at = after.findIndex((l) => idOfRow(l) === 'T-0002'); check('the owner\'s placement is never redirected', idOfRow(after[at + 1]) === id); } });

filed('a loop follow-up --after a band-10 ticket', ['A reading that belongs beside another reading', '--after', 'T-0005', '--by', 'loop'], {
  check(APP, id, after) { const at = after.findIndex((l) => idOfRow(l) === 'T-0005'); check('an anchor BELOW band 9 is honoured as before', idOfRow(after[at + 1]) === id); } });

filed('--blocks with no reason', ['A claim of blocking with nothing behind it', '--after', 'T-0002', '--by', 'loop', '--blocks'], {
  check() { check('an empty --blocks is refused', false, 'it was accepted'); },
  refused(out) { check('an empty --blocks is refused, and says what to write', /--blocks. was written with no reason/.test(out), out.trim().split('\n')[0]); } });

console.log(`\n${failures === 0 ? 'ticket --after self-test: all pass' : `ticket --after self-test: ${failures} FAILURE(S)`}`);
process.exit(failures === 0 ? 0 : 1);
