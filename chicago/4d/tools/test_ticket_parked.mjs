#!/usr/bin/env node
/**
 * test_ticket_parked.mjs — `ticket.mjs board --pr-json` puts every open pull request
 * carrying `hold` or `resume` on the board, with the reason it was parked for and how
 * long it has been sitting there, and says so out loud when it could not read the list.
 *
 * WHY THIS EXISTS (T-1571 → T-1574 → T-1576). Every automated pass in this repository
 * skips a parked pull request ON PURPOSE — `pr-lap.sh`, `merge-ready.sh` and
 * `pr-stuck.sh` all read labels before they read state — so a parked PR is by
 * construction the one kind nothing is coming back for. The only place its reason was
 * written was the PR body. The owner, on 2026-09-25, finding three at once:
 * *"that seems like a bad move because i am not aware of why they are held"*.
 *
 * WHY A FIXTURE AND NOT THE LIVE REPOSITORY. The same reason `landed --pr-json` and
 * `inflight --branches-json` take one: against the real remote the right answer changes
 * by the hour, so what the gate can assert is the READING and not the day. The fixture
 * goes through `normalizePull`, exactly as GitHub's own answer does — a fixture richer
 * than production is the T-1427 fault and it stood green for three days.
 *
 * THE READING THIS PROTECTS ABOVE ALL is case 8. A section that is empty because the
 * queue is clear and a section that is empty because the call failed print identically,
 * and the second one is a silence dressed as an all-clear — which is the exact shape of
 * the fault the whole ticket was filed about.
 *
 * The sandbox is test_ticket_inflight.mjs's: ticket.mjs resolves its paths from its own
 * location, so a temporary tree beside a copy of the tool is a whole world for it to be
 * wrong in, and the real queue is never touched.
 */
import { mkdtempSync, mkdirSync, rmSync, writeFileSync, readFileSync, cpSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const REPO = path.resolve(HERE, '..');

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

const ticketFile = (id, title, state) => `---
id: ${id}
title: ${title}
state: ${state}
epic: META
requested_by: loop
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

const TICKETS = [
  ['T-1521', 'The ticket whose PR the owner parked while dev was red', 'review'],
  ['T-1563', 'The ticket whose run ran out of clock', 'review'],
  ['T-1545', 'The ticket whose PR is moving normally', 'review'],
  ['T-0900', 'The ticket whose PR was re-parked on a second head', 'review'],
];

/** ISO for `h` hours ago, so every age in the fixture is relative to the run. */
const ago = (h) => new Date(Date.now() - h * 3.6e6).toISOString();

/* GitHub's OWN shape for each row — labels as objects, `body`, `html_url` — because
 * the whole value of the fixture is that it travels the road the API's answer does. */
const PULLS = [
  // 1. A `hold` whose body carries today's real shape: the `### Why this is on `hold``
  //    section #41, #39 and #42 all had on 2026-09-25. Road 3.
  {
    number: 41, state: 'open', title: 'T-1521: the lap publishes the mirror before the rebuild',
    created_at: ago(30), updated_at: ago(4), html_url: 'https://github.com/kevinrhaas/chicago/pull/41',
    labels: [{ name: 'hold' }], head: { ref: 'steward/t-1521-lap-publish-before-rebuild' },
    body: [
      '## What this does', '', 'It publishes the mirror first.', '',
      '### Why this is on `hold`, and what lifts it', '',
      "Dev's own gate is red on T-1567 and the red is not mine to fix inside this unit.",
      'Lift the hold when T-1567 lands.', '',
      '## Verification', '', 'The full gate, green.',
    ].join('\n'),
  },
  // 2. A `resume` with T-1573's structured comment line. Road 1, and the one that
  //    carries a `waits on`.
  {
    number: 39, state: 'open', title: 'T-1563: the first nineteen re-family moves',
    created_at: ago(6.5), updated_at: ago(0.5), html_url: 'https://github.com/kevinrhaas/chicago/pull/39',
    labels: [{ name: 'resume' }], head: { ref: 'steward/t1563-spend-trade-refamily' },
    body: 'The spender writes the ledger.\n',
  },
  // 3. An open PR with no park label at all — the control. It must not appear.
  {
    number: 45, state: 'open', title: 'T-1545: the last two West Division roofs are re-dealt',
    created_at: ago(2), updated_at: ago(0.2), html_url: 'https://github.com/kevinrhaas/chicago/pull/45',
    labels: [], head: { ref: 'steward/t1545-jefferson-corridor-redeal' },
    body: 'Re-dealt off the corridor.\n',
  },
  // 4. A park with NO reason anywhere. It must be listed and said to have none —
  //    never quietly dropped, and never given a reason it did not write.
  {
    number: 40, state: 'open', title: 'T-0900: the north corridors',
    created_at: ago(75), updated_at: ago(75), html_url: 'https://github.com/kevinrhaas/chicago/pull/40',
    labels: [{ name: 'hold' }], head: { ref: 'steward/t-0900-north-corridors' },
    body: 'Nothing about why this is parked.\n',
  },
  // 5. #42's real shape on 2026-09-25: the section's first paragraph ends on a COLON
  //    and the thought it opens is finished by the next block. A reason cut off there
  //    reads as a fragment, so the reading carries on to the end of the sentence.
  {
    number: 43, state: 'open', title: "T-1565: the lap's two entry guards report which step failed",
    created_at: ago(2), updated_at: ago(2), html_url: 'https://github.com/kevinrhaas/chicago/pull/43',
    labels: [{ name: 'hold' }], head: { ref: 'steward/t1565-lap-checkout-evidence' },
    body: [
      '### Why this is on `hold`', '',
      '`./tools/check.sh` is **red on `dev` itself**, for reasons this branch does not touch. Four steps:', '',
      'the datum re-derivation, the licence sweep, the staleness gate and the JS parse.', '',
      '```', 'the fence that must never be flattened onto the board line', '```', '',
      '## Verification', '', 'Not reached.',
    ].join('\n'),
  },
  // 6. A CLOSED PR carrying `hold`. Closed is not parked.
  {
    number: 12, state: 'closed', title: 'T-1111: long gone', merged_at: ago(200),
    created_at: ago(300), updated_at: ago(200), html_url: 'https://github.com/kevinrhaas/chicago/pull/12',
    labels: [{ name: 'hold' }], head: { ref: 'steward/t-1111-gone' },
    body: '### Why this is on `hold`\n\nIt was, once.\n',
  },
];

const COMMENTS = {
  39: [
    { created_at: ago(5), body: 'resume: the run\'s clock ran out before the full gate · waits on: nothing' },
    // NEWER, and it is the one that must win: a PR re-parked on a second head has a
    // second line and the stale one is not the state of play.
    { created_at: ago(0.5), body: "resume: dev's gate is red and this branch inherits it · waits on: T-1567" },
  ],
  41: [{ created_at: ago(20), body: 'Lapped onto current dev.' }],
};

function sandbox() {
  const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-parked-'));
  const APP = path.join(tmp, 'chicago', '4d');
  mkdirSync(path.join(APP, 'tools'), { recursive: true });
  mkdirSync(path.join(APP, 'tickets'), { recursive: true });
  cpSync(path.join(REPO, 'tools', 'ticket.mjs'), path.join(APP, 'tools', 'ticket.mjs'));
  const queue = [];
  for (const [id, title, state] of TICKETS) {
    writeFileSync(path.join(APP, 'tickets', `${id}-fixture.md`), ticketFile(id, title, state));
    queue.push(`${id} — ${title}`);
  }
  writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'),
    '# QUEUE — top is next. THE OWNER ORDERS THIS FILE.\n\n' + queue.join('\n') + '\n');
  return { tmp, APP };
}

function board(APP, fixture) {
  const file = path.join(APP, 'pulls.json');
  const extra = [];
  if (fixture !== undefined) {
    writeFileSync(file, JSON.stringify(fixture, null, 2));
    extra.push('--pr-json', file);
  }
  const r = spawnSync('node',
    [path.join(APP, 'tools', 'ticket.mjs'), 'board', ...extra, '--json'],
    { cwd: APP, encoding: 'utf8' });
  const out = `${r.stdout ?? ''}${r.stderr ?? ''}`;
  return {
    status: r.status, out,
    md: readFileSync(path.join(APP, 'tickets', 'BOARD.md'), 'utf8'),
    json: JSON.parse(readFileSync(path.join(APP, 'tickets', 'tickets.json'), 'utf8')),
  };
}

/* ------------------------------------------- 1-8: the constructed pull-request list */

{
  const { tmp, APP } = sandbox();
  try {
    console.log('\n  a constructed pull-request list, no network, ticket.mjs board --pr-json');
    const { status, md, json } = board(APP, { pulls: PULLS, comments: COMMENTS });
    const rows = json.parked?.pulls ?? [];
    const row = (n) => rows.find((r) => r.number === n);

    check('0. the command succeeded and the board was written', status === 0 && md.length > 0);

    check('1. THE FAULT: a held PR is on the board at all, with its number and its label',
      !!row(41) && row(41).label === 'hold'
      && /\*\*\[#41\]\(https:\/\/github\.com\/kevinrhaas\/chicago\/pull\/41\)\*\* `hold`/.test(md));

    check('   …and its reason is the one its body wrote, read verbatim and not composed',
      row(41)?.reason === "Dev's own gate is red on T-1567 and the red is not mine to fix inside this unit."
        + ' Lift the hold when T-1567 lands.'
      && row(41)?.reason_from === 'body-section'
      && md.includes('Lift the hold when T-1567 lands.'),
      JSON.stringify(row(41)?.reason));

    check('   …and its age is on the board, so "how long has this been invisible" is answerable',
      row(41)?.age === '30h' && /open 30h, last touched 4h ago/.test(md),
      `${row(41)?.age} / ${row(41)?.idle}`);

    check('2. a `resume` PR is on the board too, and is named as work the loop still owes',
      row(39)?.label === 'resume' && /`resume`[\s\S]{0,120}work the loop still owes/.test(md));

    check('   …its reason comes from the NEWEST structured comment, not the stale one',
      row(39)?.reason === "dev's gate is red and this branch inherits it"
      && row(39)?.reason_from === 'comment',
      JSON.stringify(row(39)?.reason));

    check('   …and the ticket it waits on is carried through, because the run named it',
      row(39)?.waits_on === 'T-1567' && /\*\*waits on:\*\* T-1567/.test(md));

    check('3. an open PR with neither label is not on the board — the labels are the filter',
      !row(45) && !md.includes('#45'));

    check('4. a park with no reason written anywhere is LISTED and said to have none',
      !!row(40) && row(40).reason === null && row(40).reason_from === null
      && /_no reason written on the PR_/.test(md));

    check('5. a reason that stops on a colon is carried to the end of its thought,'
      + ' and never past the next heading or into a code fence',
      row(43)?.reason === '`./tools/check.sh` is **red on `dev` itself**, for reasons this'
        + ' branch does not touch. Four steps: the datum re-derivation, the licence sweep,'
        + ' the staleness gate and the JS parse.'
      && !/Not reached|never be flattened/.test(row(43)?.reason ?? ''),
      JSON.stringify(row(43)?.reason));

    check('6. a closed pull request is not a parked one however it is labelled',
      !row(12) && !md.includes('#12'));

    check('7. the ticket each PR belongs to is resolved from its title',
      row(41)?.ticket === 'T-1521' && row(39)?.ticket === 'T-1563',
      `${row(41)?.ticket} / ${row(39)?.ticket}`);

    check('8. oldest first — the one parked longest has been invisible longest',
      rows.map((r) => r.number).join(',') === '40,41,39,43',
      rows.map((r) => r.number).join(','));

    check('   …and the section sits ABOVE the queue, where the owner looks first',
      md.indexOf('Parked pull requests') > 0
      && md.indexOf('Parked pull requests') < md.indexOf('In the queue'));

    check('   …counted in the heading, so the board states how many there are',
      /## ⏸ Parked pull requests — nothing automated will move these \(4\)/.test(md));
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* ------------------------------------------------ 9-11: the readings about nothing */

{
  const { tmp, APP } = sandbox();
  try {
    console.log('\n  an empty list, an unreadable list, and no question asked at all');

    const clear = board(APP, { pulls: PULLS.filter((p) => p.number === 45), comments: {} });
    check('9. nothing parked says so POSITIVELY — a bare empty section is what an'
      + ' unread list also looks like',
      /## ⏸ Parked pull requests \(0\)/.test(clear.md)
      && /Nothing is parked/.test(clear.md)
      && clear.json.parked?.ok === true && clear.json.parked.pulls.length === 0);

    // The shape a rate limit or a 404 arrives in: `restGet` answers null, and this is
    // the one case that must not read as an all-clear.
    // `pulls: null` is the fixture's only way to reach the branch `restGet` reaches
    // on a rate limit, a 404 or no network — see collectParked's note on UNREADABLE.
    const blind = board(APP, { pulls: null, comments: {} });
    check('10. THE SILENCE THAT MATTERS: a list that could not be read is reported as'
      + ' NOT READ, never as "nothing is parked"',
      /## ⏸ Parked pull requests — NOT READ/.test(blind.md)
      && /This is not \*\*"nothing is parked"\*\*|not "nothing is parked"/.test(blind.md)
      && blind.json.parked?.ok === false,
      JSON.stringify(blind.json.parked?.ok));

    const unasked = board(APP);
    check('11. `board` with no --parked and no fixture asks nothing and claims nothing —'
      + ' publish.sh and the lap stay offline',
      !unasked.md.includes('Parked pull requests')
      && !('parked' in unasked.json),
      Object.keys(unasked.json).join(','));

    check('    …and the tickets it always carried are untouched by all of it',
      Array.isArray(unasked.json.tickets) && unasked.json.tickets.length === TICKETS.length
      && unasked.json.project === 'chicago-4d');
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

console.log(`\n  ${failures === 0 ? 'parked pull requests: every reading holds' : `${failures} FAILED`}`);
process.exit(failures === 0 ? 0 : 1);
