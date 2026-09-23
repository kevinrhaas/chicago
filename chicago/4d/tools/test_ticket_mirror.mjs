#!/usr/bin/env node
/**
 * test_ticket_mirror.mjs — closing a ticket does not leave the published mirror
 * stale, AND the gate that catches a genuinely stale mirror still catches one.
 *
 * WHY THIS EXISTS (T-0154). `site/chicago/4d/tickets.json` is a verbatim copy of
 * `tickets/tickets.json`, and `tools/check_published.mjs` compares the two byte
 * for byte. `ticket.mjs done` rewrites the source. So the order AGENTS.md states
 * — publish in the same commit, then push, then close the ticket in the merging
 * PR with the number that push just produced — ended red every single time, and
 * what actually held it together was a REMEMBERED extra `publish.sh` after the
 * close. That is the kind of unwritten step that goes wrong at 3am, and it did:
 * T-0153/PR #318, gate red at 05:11Z on exactly this.
 *
 * The fix is that the writer of the file maintains its mirror. The DANGER in that
 * fix is obvious and the ticket's acceptance names it: a tool that refreshes the
 * mirror whenever it runs would launder a genuinely stale mirror, and the fault
 * class this gate exists for (#145, three parcels) would be invisible again. So
 * this file asserts BOTH halves, and the second one is the important one.
 *
 * EVERYTHING RUNS IN A SANDBOX. The tools resolve their paths from their own
 * location, so a temporary tree of the shape they expect — `<tmp>/chicago/4d/…`
 * beside `<tmp>/site/chicago/4d/` — gives them a whole world to be wrong in
 * without touching the repository. An earlier draft of this test mutated the real
 * tickets.json and restored it afterwards; a crash in the middle of that leaves a
 * working tree nobody can explain, which is not a thing to build a gate on.
 */
import { mkdtempSync, mkdirSync, cpSync, rmSync, readFileSync, writeFileSync,
  existsSync } from 'node:fs';
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

/* ------------------------------------------------------------------ sandbox */

const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-ticket-mirror-'));
const APP = path.join(tmp, 'chicago', '4d');
const SITE = path.join(tmp, 'site', 'chicago', '4d');
mkdirSync(path.join(APP, 'tools'), { recursive: true });
mkdirSync(SITE, { recursive: true });
// The three tools under test, and the ticket files they read. Nothing else: the
// sandbox site holds one file, so check_published has exactly one thing to say.
for (const f of ['ticket.mjs', 'check_published.mjs', 'publish.sh']) {
  cpSync(path.join(REPO, 'tools', f), path.join(APP, 'tools', f));
}
cpSync(path.join(REPO, 'tickets'), path.join(APP, 'tickets'), { recursive: true });

const SRC = path.join(APP, 'tickets', 'tickets.json');
const MIRROR = path.join(SITE, 'tickets.json');
const BOARD = path.join(APP, 'tickets', 'BOARD.md');

// stderr is CAPTURED, not inherited: half of what runs below is expected to fail,
// and a gate whose green log is full of other tools' FAILED banners teaches whoever
// reads it to ignore banners.
const RUN = { cwd: APP, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] };
const said = (e) => `${e.stdout ?? ''}${e.stderr ?? ''}`;
const ticket = (...args) => execFileSync('node', [path.join(APP, 'tools', 'ticket.mjs'), ...args], RUN);
/** The gate, as a boolean plus what it said. */
const published = () => {
  try {
    return { ok: true, out: execFileSync('node',
      [path.join(APP, 'tools', 'check_published.mjs')], RUN) };
  } catch (e) {
    return { ok: false, out: said(e) };
  }
};

try {
  console.log(`ticket mirror — sandbox at ${tmp}`);

  /* --- half zero: an UNBUILT tree builds itself (T-0937) ----------------- */
  //
  // BOARD.md, tickets.json and the mirror are untracked as of T-0937 — they were
  // the most-conflicting files in the repository, because a run's first act is
  // `ticket.mjs claim` and that rewrites all three before any work is done. So a
  // fresh clone and every CI checkout now start with NONE of them, and each reader
  // has to be able to make its own.
  //
  // This half exists because the regression is silent in the worst possible way:
  // on a developer's machine the three files survive from the last run, so the gate
  // stays green while a CI checkout publishes no /chicago/4d/tickets.json at all —
  // and that URL is Manager's queue card (T-0030). Nobody would see a red.
  //
  // The mirror assertion is the sharp one. `mirrorTickets` deliberately copies only
  // when the source was actually rewritten, so that a mirror somebody else made
  // stale is never laundered (half two below). An absent mirror is not a stale one,
  // and it must be filled anyway — that is the case this line pins.
  for (const f of [SRC, BOARD, MIRROR]) if (existsSync(f)) rmSync(f);
  ticket('board');
  check('an unbuilt tree generates tickets.json', existsSync(SRC));
  check('…and BOARD.md', existsSync(BOARD));
  check('…and the published mirror, though nothing rewrote the source before it',
    existsSync(MIRROR) && readFileSync(MIRROR, 'utf8') === readFileSync(SRC, 'utf8'),
    existsSync(MIRROR) ? 'mirror matches source' : 'mirror absent');

  // A published tree: the board regenerated, then copied the way publish.sh
  // copies it. This is the state every run is in when it reaches step 2.
  ticket('board');
  writeFileSync(MIRROR, readFileSync(SRC));
  check('a freshly published sandbox passes the mirror gate', published().ok);

  // The ticket to close. Any workable one; the queue's own order picks it, so
  // this test does not care which tickets exist.
  const workable = ticket('list', '--workable').trim().split('\n').filter(Boolean);
  const victim = workable[0]?.split(/\s+/)[0];
  check('the sandbox queue offers a ticket to close', /^T-\d{4}$/.test(victim ?? ''), victim);

  /* --- half one: the documented order ends green ------------------------- */
  //
  // Exactly the sequence in AGENTS.md, from the point publish.sh has run: push,
  // open the PR, close the ticket with the number the PR just got. No second
  // publish, because a run following the documented steps does not do one.
  ticket('done', victim, '--pr', '9999');
  const afterClose = published();
  check('closing a ticket leaves the published mirror fresh', afterClose.ok,
    afterClose.ok ? 'no remembered publish.sh needed' : afterClose.out.trim().split('\n').pop());
  check('…and the mirror really is the closed board, not the old one',
    readFileSync(MIRROR, 'utf8') === readFileSync(SRC, 'utf8')
      && readFileSync(MIRROR, 'utf8').includes('"pr": "9999"'),
    `${readFileSync(MIRROR, 'utf8').length} bytes`);

  // THE FINISH ORDER IS A FACT THE MIRROR CARRIES. `closed` is a day, so two
  // tickets finished on the same day used to sort by ticket id — the board read
  // as if the work had been done alphabetically. `done` now stamps the instant,
  // and the board's finished section leads with the ticket that just closed.
  const mirror = JSON.parse(readFileSync(MIRROR, 'utf8'));
  const closedTicket = mirror.tickets.find((t) => t.id === victim);
  check('the closed ticket carries the instant it finished, not only the day',
    !!closedTicket?.closed_at && !Number.isNaN(Date.parse(closedTicket.closed_at)),
    closedTicket?.closed_at ?? 'closed_at absent');
  const finishedHead = /## Finished, newest first[^\n]*\n\n- \*\*(T-\d{4})\*\*/
    .exec(readFileSync(BOARD, 'utf8'));
  check('and the board lists it first under Finished, newest first',
    finishedHead?.[1] === victim, finishedHead ? `leads with ${finishedHead[1]}` : 'no such section');

  /* --- half two: the gate is not weaker ---------------------------------- */
  //
  // This is the half the acceptance clause insists on. A mirror somebody else
  // made stale — a hand edit, a bad merge, a publish that half-ran — must still
  // fail, and running the ticket tool over it must NOT quietly repair it. If a
  // no-op regeneration laundered the mirror, the gate would be reporting on the
  // tool's own last act rather than on what the site ships.
  writeFileSync(MIRROR, `${readFileSync(MIRROR, 'utf8')}\n// hand-edited\n`);
  const dirtied = published();
  check('a hand-staled mirror still fails the gate', !dirtied.ok,
    dirtied.out.includes('tickets.json DIFFERS') ? 'and it names tickets.json' : 'WITHOUT naming it');

  ticket('board');   // a regeneration that changes nothing in the source
  const afterNoop = published();
  check('a no-op regeneration does NOT launder that stale mirror', !afterNoop.ok,
    afterNoop.ok ? 'the mirror was silently repaired — the gate has been weakened' : 'still red');

  writeFileSync(MIRROR, readFileSync(SRC));
  check('and republishing clears it again', published().ok);

  /* --- the pin: two copies of one fact cannot drift ---------------------- */
  //
  // ticket.mjs hard-codes where publish.sh puts this file. `check` pins the copy
  // line so the pair cannot drift into mirroring different paths in silence.
  const pubSh = path.join(APP, 'tools', 'publish.sh');
  const kept = readFileSync(pubSh, 'utf8');
  writeFileSync(pubSh, kept.replace('cp -f tickets/tickets.json "$SITE/tickets.json"',
    'cp -f tickets/tickets.json "$SITE/board/tickets.json"'));
  let pinned = '';
  try { ticket('check'); } catch (e) { pinned = said(e); }
  check('moving publish.sh\'s copy is refused by `ticket.mjs check`',
    pinned.includes('no longer contains'),
    pinned ? 'and it names the reconciliation' : 'check stayed green');
  writeFileSync(pubSh, kept);
} finally {
  if (existsSync(tmp)) rmSync(tmp, { recursive: true, force: true });
}

console.log(failures ? `ticket mirror FAILED — ${failures} assertion(s)` : 'ticket mirror OK');
process.exit(failures ? 1 : 0);
