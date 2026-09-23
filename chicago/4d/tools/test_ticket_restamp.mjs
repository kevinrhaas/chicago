#!/usr/bin/env node
/**
 * test_ticket_restamp.mjs — `restamp` renumbers ONE ticket and rewrites ONE queue
 * line: the line belonging to the file it was handed. The other ticket's line,
 * which the owner ranked, is left exactly where and as it was.
 *
 * WHY THIS EXISTS (T-0217). `restamp` is the duplicate-id remedy, so the ONLY
 * state it ever runs in is the one where two ticket files carry the same id — and
 * therefore two queue lines do too. Its own comment says the FILE is the only way
 * to name which of the pair moves, "with two files sharing an id, `find` by id
 * cannot tell them apart". Two lines later the queue edit went back to matching on
 * the id:
 *
 *     const line = queueIds().indexOf(old);        // FIRST line carrying that id
 *     if (line >= 0) queueReplace(old, [...]);     // …and the first one again
 *
 * With a duplicate there are two, so which one moved was whichever the owner had
 * ranked higher — a coin toss. On 2026-08-27, during T-0215's merge, it came up
 * tails: dev's `T-0211 — The other nine group rows…` line was overwritten with
 * this run's title, and this run's own line was left behind carrying a stale id.
 * A real ticket vanished from the queue and a phantom stayed in it. **Every gate
 * was green**; it was caught by a human reading `tail QUEUE.md`, and repaired by
 * hand.
 *
 * So this file asserts three things, and the second is the one with teeth:
 *   1. the file's own line is the one that moves, and it keeps its rank;
 *   2. it is not position luck — the same fixture with the two lines SWAPPED must
 *      still move the right one. The old code passes (1) half the time by
 *      accident, and fails (2) on one of the two orderings every time;
 *   3. `check` now names both conditions that survived the bug silently — a queue
 *      line whose id is not in the ledger, and a line whose label names a
 *      different ticket than its id does.
 *
 * EVERYTHING RUNS IN A SANDBOX, for the reason test_ticket_mirror.mjs states: the
 * tool resolves its paths from its own location, so a temporary `<tmp>/tickets/`
 * beside a copy of the tool is a whole world for it to be wrong in. This test
 * builds its ticket files from scratch rather than copying the repository's — the
 * fixture has to hold a duplicate id, which is a state the real tree must never be
 * committed in, and a test that mutates the real queue and restores it afterwards
 * leaves an unexplainable working tree if it dies in the middle.
 */
import { mkdtempSync, mkdirSync, rmSync, cpSync, readFileSync, writeFileSync,
  readdirSync, existsSync } from 'node:fs';
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

/** A minimal ticket file — only the fields `check` insists on. */
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
opened: 2026-08-27
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

${title}.

**Acceptance:** fixture.
`;

// The pair from the incident, by their real titles, plus a third ticket ranked
// between them: the owner's order is the thing being protected, so the fixture
// has to be able to show it surviving.
const DEV = 'The other nine group rows are cross-checked against nothing';
const MINE = 'Desktop smoke stage 8 (What’s-new) is red on dev';
const OTHER = 'A third ticket the owner ranked between them';

/**
 * A sandbox holding two files that both claim T-0211, and a queue whose lines are
 * in `order`. Returns the paths the test needs.
 */
function sandbox(order) {
  const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-restamp-'));
  const APP = path.join(tmp, 'chicago', '4d');
  mkdirSync(path.join(APP, 'tools'), { recursive: true });
  mkdirSync(path.join(APP, 'tickets'), { recursive: true });
  cpSync(path.join(REPO, 'tools', 'ticket.mjs'), path.join(APP, 'tools', 'ticket.mjs'));

  const T = (f, body) => writeFileSync(path.join(APP, 'tickets', f), body);
  T('T-0211-the-other-nine-group-rows.md', ticketFile('T-0211', DEV));
  T('T-0211-desktop-smoke-stage-8.md', ticketFile('T-0211', MINE));
  T('T-0212-a-third-ticket.md', ticketFile('T-0212', OTHER));

  writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'),
    '# QUEUE — top is next. THE OWNER ORDERS THIS FILE.\n\n'
    + `${order.map(([id, title]) => `${id} — ${title}`).join('\n')}\n`);
  return { tmp, APP, mine: path.join(APP, 'tickets', 'T-0211-desktop-smoke-stage-8.md') };
}

const RUN = (APP) => ({ cwd: APP, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
const said = (e) => `${e.stdout ?? ''}${e.stderr ?? ''}`;
const tool = (APP, ...args) => execFileSync('node',
  [path.join(APP, 'tools', 'ticket.mjs'), ...args], RUN(APP));
/** `check` as a boolean plus what it said — half the calls below expect a red. */
function checkTool(APP) {
  try { return { ok: true, out: tool(APP, 'check') }; } catch (e) { return { ok: false, out: said(e) }; }
}
const queueRows = (APP) => readFileSync(path.join(APP, 'tickets', 'QUEUE.md'), 'utf8')
  .split('\n').map((l) => l.trim()).filter((l) => /^T-\d{4}\b/.test(l));

/* ---------------------------------------------- 1 & 2: the right line moves */

/**
 * Restamp the younger file with the queue in `order`, and assert the outcome.
 * `mineAt` is where this run's line sits, 0-based, so the assertions can say
 * "kept its rank" rather than "is somewhere in the file".
 */
function restampWith(label, order, mineAt) {
  const { tmp, APP, mine } = sandbox(order);
  try {
    console.log(`\n  ${label}`);
    const out = tool(APP, 'restamp', mine);
    const newId = /T-0211 → (T-\d{4})/.exec(out)?.[1];
    check('the younger file is renumbered', /^T-\d{4}$/.test(newId ?? '') && newId !== 'T-0211',
      newId ?? out.trim());

    const rows = queueRows(APP);
    check('the queue still holds one line per ticket', rows.length === order.length,
      `${rows.length} line(s): ${rows.join(' | ')}`);

    // THE ASSERTION. The line that moved is the one whose label was written from
    // the restamped file, and it moved in place.
    check('this run\'s line took the new id, in its own rank',
      rows[mineAt] === `${newId} — ${MINE}`,
      `line ${mineAt + 1} reads "${rows[mineAt]}"`);

    // AND THE ONE THAT DID NOT. Under the old code this line read
    // `T-0215 — Desktop smoke stage 8 …`: another ticket's id, another ticket's
    // title, and the ticket it named nowhere in the queue at all.
    const devAt = order.findIndex(([, title]) => title === DEV);
    check('the OTHER T-0211 line is untouched — id and title both',
      rows[devAt] === `T-0211 — ${DEV}`,
      `line ${devAt + 1} reads "${rows[devAt]}"`);

    // The owner's ranking is what all of this is protecting.
    const otherAt = order.findIndex(([, title]) => title === OTHER);
    check('the unrelated ticket keeps its rank', rows[otherAt] === `T-0212 — ${OTHER}`,
      `line ${otherAt + 1}`);

    // The renumbered file exists under its new id, and the old name is gone.
    const files = readdirSync(path.join(APP, 'tickets'));
    check('the file was renamed with it', files.some((f) => f.startsWith(`${newId}-`))
      && !files.includes('T-0211-desktop-smoke-stage-8.md'), files.filter((f) => /^T-/.test(f)).join(', '));

    // The whole point: after the repair the tree is clean, with no hand editing.
    const after = checkTool(APP);
    check('and `check` is green afterwards, with nothing repaired by hand', after.ok,
      after.ok ? after.out.trim() : after.out.trim().split('\n').slice(-3).join(' / '));
  } finally {
    if (existsSync(tmp)) rmSync(tmp, { recursive: true, force: true });
  }
}

console.log('ticket restamp — the duplicate-id repair moves the line it was handed');

// Both orderings. The old code moved line 1 whichever ticket owned it, so exactly
// one of these two passed — and which one was down to how the owner had ranked
// them, which is not a property a repair tool may depend on.
restampWith('dev’s line ranked FIRST (the ordering that failed on 2026-08-27)',
  [['T-0211', DEV], ['T-0212', OTHER], ['T-0211', MINE]], 2);
restampWith('this run’s line ranked FIRST (the ordering that passed by luck)',
  [['T-0211', MINE], ['T-0212', OTHER], ['T-0211', DEV]], 0);

/* ------------------------------------ 3: check names what survived silently */

console.log('\n  the conditions that used to survive a wrong-line restamp');
{
  const { tmp, APP } = sandbox([['T-0211', DEV], ['T-0212', OTHER], ['T-0211', MINE]]);
  try {
    // A queue line pointing at an id no ticket file carries — the phantom the bug
    // left behind. Written here directly, because the fixed restamp cannot make one.
    writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'),
      `# QUEUE\n\nT-0211 — ${DEV}\nT-0212 — ${OTHER}\nT-0999 — a line naming nothing\n`);
    rmSync(path.join(APP, 'tickets', 'T-0211-desktop-smoke-stage-8.md'));
    const ghost = checkTool(APP);
    check('a queue line whose id is not in the ledger is refused', !ghost.ok
      && ghost.out.includes('T-0999') && ghost.out.includes('not in the ledger'),
      ghost.ok ? 'check stayed GREEN' : 'and it names T-0999');

    // A line carrying one ticket's id and another's title. Every id gate is green
    // on this: both ids are real, both open, neither duplicated.
    writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'),
      `# QUEUE\n\nT-0211 — ${MINE}\nT-0212 — ${OTHER}\n`);
    const mislabelled = checkTool(APP);
    check('a queue line labelled with ANOTHER ticket’s title is refused', !mislabelled.ok
      && mislabelled.out.includes('T-0211') && mislabelled.out.includes('the ticket wins'),
      mislabelled.ok ? 'check stayed GREEN' : 'and it quotes the line it should read');

    // …and the gate is not just "any label I do not recognise": the true labels pass.
    writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'),
      `# QUEUE\n\nT-0211 — ${DEV}\nT-0212 — ${OTHER}\n`);
    const clean = checkTool(APP);
    check('and the correctly-labelled queue is green', clean.ok,
      clean.ok ? clean.out.trim() : clean.out.trim().split('\n').slice(-3).join(' / '));
  } finally {
    if (existsSync(tmp)) rmSync(tmp, { recursive: true, force: true });
  }
}

console.log(failures ? `\nticket restamp FAILED — ${failures} assertion(s)` : '\nticket restamp OK');
process.exit(failures ? 1 : 0);
