#!/usr/bin/env node
/**
 * test_ticket_landed.mjs — `ticket.mjs landed` names the tickets whose PR already
 * merged, and refuses to name anything else.
 *
 * WHY THIS EXISTS (T-0802). Everything in this repository squash-merges, so a merged
 * branch never becomes an ancestor of `dev` and git cannot be asked whether work
 * landed. `inflight` says so itself and falls back on branch AGE, which means a run
 * that died between its merge and `ticket.mjs done` leaves a ticket sitting `claimed`
 * behind a COLD branch — and cold reads as litter, not as done. T-0429 sat that way
 * for five days as the topmost queue line carrying no PR, which is exactly the shape
 * of available work, and `steward/t-0429-south-water-lasalle` rebuilt the whole block
 * — 116 files, 5,827 insertions, baked — onto records that already existed on `dev`.
 *
 * WHY THE TEST IS A FIXTURE AND NOT A LIVE READ. The acceptance clause asks for one
 * demonstration, never weakened to pass. A check whose correct answer against the real
 * `dev` changes every hour cannot be that demonstration: it would assert nothing on a
 * clean day and fail the gate on a dirty one, for a report that is forbidden to fail
 * anything. So `landed --pr-json` reads a CONSTRUCTED pull-request list, and the cases
 * below are the ones that decide whether the check is trustworthy:
 *
 *   1. a `claimed` ticket whose PR merged IS reported, with its number and instant —
 *      T-0429's own shape, which is the fault this exists to catch;
 *   2. a ticket whose PR is still OPEN is not — a PR that has not merged is not
 *      evidence of anything;
 *   3. a ticket nobody's PR names is not, and the tool says plainly that silence is
 *      not a clean bill of health;
 *   4. `done` is not reported — every closed ticket has a merged PR naming it, which
 *      would otherwise be one finding per closed ticket forever;
 *   5. nor is `blocked-owner`, for the same structural reason: a run BLOCKS in the
 *      merging PR exactly as it closes in one, so every blocked ticket in the repo is
 *      named by a merged PR by design, and none of them is offered as work;
 *   6. A QUEUE-KEEPING TITLE IS NOT A CLAIM OF AUTHORSHIP. "File T-0968: …", "Pull
 *      T-0802 up into the blocking band", "Rank T-0727 under the drain band" are three
 *      real merged PRs in this repository that touched none of the work they name, and
 *      the first draft of this check accused all three. The id must START the title;
 *   7. nor is an id in the PROSE after the colon — "T-0995: the shared roll lines
 *      T-0992's spend leaves unsaid" is not a statement about T-0992;
 *   8. a paired title (`T-0867/T-0868: …`) names BOTH, because one PR closing two is
 *      a convention this lane actually uses;
 *   9. the near-miss a number match invites: T-0042 must not fire on `T-0429`, and
 *      `T-429` unpadded must still read as T-0429;
 *  10. IT EXITS 0 WHATEVER IT FINDS. A gate that hard-fails on a naming convention
 *      blocks a run that did nothing wrong, and the tool must say so in its output.
 *
 * EVERYTHING RUNS IN A SANDBOX, as test_ticket_after.mjs explains: ticket.mjs resolves
 * its paths from its own location, so a temporary tree beside a copy of the tool is a
 * whole world for it to be wrong in, and the real queue is never touched. No network
 * is reachable from any case here, which is the point.
 */
import { mkdtempSync, mkdirSync, rmSync, writeFileSync, cpSync } from 'node:fs';
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

/* ------------------------------------------------------------------ fixture */

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
closed: ${state === 'done' ? '2026-09-02' : 'null'}
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

// id, title, state, and whether the queue carries it (only workable states do).
const TICKETS = [
  ['T-0429', 'The claimed ticket whose run died after the merge', 'claimed'],
  ['T-0042', 'The near miss a number match invites', 'open'],
  ['T-0520', 'The ticket whose PR is still open', 'open'],
  ['T-0727', 'The ticket a queue-keeping PR only re-ranked', 'open'],
  ['T-0802', 'The ticket a queue-keeping PR only pulled up', 'open'],
  ['T-0968', 'The ticket a queue-keeping PR only filed', 'open'],
  ['T-0992', 'The ticket named in another PR title’s prose', 'open'],
  ['T-0867', 'The first half of a paired PR', 'open'],
  ['T-0868', 'The second half of a paired PR', 'open'],
  ['T-1000', 'The ticket no PR has ever named', 'open'],
  ['T-0100', 'The ticket that is finished, closed by its own merged PR', 'done'],
  ['T-0841', 'The ticket a merged PR blocked on the owner', 'blocked-owner'],
];

// The constructed pull-request list. `merged_at` null = closed without merging.
const PULLS = [
  { number: 597, title: 'T-429: deepen the south water at LaSalle', merged_at: '2026-09-01T00:40:50Z', created_at: '2026-08-31T00:00:00Z' },
  { number: 1251, title: 'T-0520: one set of doors and windows', merged_at: null, created_at: '2026-09-12T00:00:00Z' },
  { number: 909, title: 'Rank T-0727 under the drain band, and restore the band the driver stripped', merged_at: '2026-09-05T19:44:25Z', created_at: '2026-09-05T00:00:00Z' },
  { number: 920, title: 'Pull T-0802 up into the blocking band, on the evidence that caught it', merged_at: '2026-09-05T21:14:51Z', created_at: '2026-09-05T00:00:00Z' },
  { number: 1032, title: 'File T-0968: a green deploy is not proof the site is reachable', merged_at: '2026-09-07T14:48:52Z', created_at: '2026-09-07T00:00:00Z' },
  { number: 1064, title: 'T-0995: the shared roll lines T-0992’s spend leaves unsaid on eleven cards', merged_at: '2026-09-10T10:33:18Z', created_at: '2026-09-10T00:00:00Z' },
  { number: 1121, title: 'T-0867/T-0868: the pair one PR closed', merged_at: '2026-09-11T00:00:00Z', created_at: '2026-09-10T00:00:00Z' },
  { number: 318, title: 'T-0100: the finished one', merged_at: '2026-09-02T00:00:00Z', created_at: '2026-09-01T00:00:00Z' },
  { number: 1090, title: 'T-0841: every church reading is read or declared', merged_at: '2026-09-11T14:50:36Z', created_at: '2026-09-11T00:00:00Z' },
  // The later follow-up on an already-reported ticket: the EARLIEST merge is the one
  // that landed the work, and the report must name #597, not this.
  { number: 1180, title: 'T-0429: a follow-up on the south water', merged_at: '2026-09-12T00:00:00Z', created_at: '2026-09-12T00:00:00Z' },
];

function sandbox() {
  const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-landed-'));
  const APP = path.join(tmp, 'chicago', '4d');
  mkdirSync(path.join(APP, 'tools'), { recursive: true });
  mkdirSync(path.join(APP, 'tickets'), { recursive: true });
  cpSync(path.join(REPO, 'tools', 'ticket.mjs'), path.join(APP, 'tools', 'ticket.mjs'));
  const queue = [];
  for (const [id, title, state] of TICKETS) {
    writeFileSync(path.join(APP, 'tickets', `${id}-fixture.md`), ticketFile(id, title, state));
    if (['open', 'claimed', 'review'].includes(state)) queue.push(`${id} — ${title}`);
  }
  writeFileSync(path.join(APP, 'tickets', 'QUEUE.md'),
    '# QUEUE — top is next. THE OWNER ORDERS THIS FILE.\n\n' + queue.join('\n') + '\n');
  writeFileSync(path.join(APP, 'pulls.json'), JSON.stringify(PULLS, null, 2));
  return { tmp, APP };
}

/** Runs the tool and keeps BOTH streams and the status — the status is half of what
 *  case 10 asserts, so it must never be allowed to throw. */
function landed(APP, ...extra) {
  const r = spawnSync('node',
    [path.join(APP, 'tools', 'ticket.mjs'), 'landed', '--pr-json', path.join(APP, 'pulls.json'), ...extra],
    { cwd: APP, encoding: 'utf8' });
  return { status: r.status, out: `${r.stdout ?? ''}${r.stderr ?? ''}` };
}

/* ------------------------------------------------ 1-10: the constructed case */

{
  const { tmp, APP } = sandbox();
  try {
    console.log('\n  a constructed PR list, no network, ticket.mjs landed');
    const { status, out } = landed(APP);
    const json = landed(APP, '--json');
    const rows = JSON.parse(/\[[\s\S]*\]\s*$/.exec(json.out)?.[0] ?? 'null');
    const named = new Set((rows ?? []).map((r) => r.id));
    const row = (id) => (rows ?? []).find((r) => r.id === id);

    check('1. the claimed ticket whose PR merged IS reported, with number and instant',
      row('T-0429')?.pr === 597 && row('T-0429')?.merged_at === '2026-09-01T00:40:50Z',
      JSON.stringify(row('T-0429')));
    check('   …and the report prints the close command a run can run',
      /done T-0429 --pr 597/.test(out), out.split('\n').find((l) => /T-0429/.test(l)));
    check('2. a ticket whose PR is still OPEN is not reported', !named.has('T-0520'));
    check('3. a ticket no PR names is not reported', !named.has('T-1000'));
    check('4. a `done` ticket is not reported, though a merged PR names it',
      !named.has('T-0100'));
    check('5. a `blocked-owner` ticket is not reported, for the same reason',
      !named.has('T-0841'));
    check('6. a queue-keeping title is not a claim of authorship (rank / pull-up / file)',
      !named.has('T-0727') && !named.has('T-0802') && !named.has('T-0968'),
      [...named].join(' '));
    check('7. an id in the PROSE after the colon is not reported', !named.has('T-0992'));
    check('8. a paired title names BOTH of its tickets',
      named.has('T-0867') && named.has('T-0868'));
    check('9. T-0042 does not fire on `T-429`, and `T-429` still reads as T-0429',
      !named.has('T-0042') && named.has('T-0429'));
    check('   …and the EARLIEST merge is the one reported, not a later follow-up',
      row('T-0429')?.pr === 597, `PR #${row('T-0429')?.pr}`);
    check('10. it exits 0 with findings — a report never fails a gate',
      status === 0 && json.status === 0, `exit ${status}`);
    check('    …and says in its own output why it does not fail',
      /never fails a gate/.test(out) && /convention/.test(out));
    check('    the exact finding set is the three expected tickets and nothing else',
      [...named].sort().join(',') === 'T-0429,T-0867,T-0868', [...named].sort().join(','));
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* ---------------------------------- 11: nothing to report is not "all clear" */

{
  const { tmp, APP } = sandbox();
  try {
    console.log('\n  a PR list that names nothing unfinished');
    writeFileSync(path.join(APP, 'pulls.json'), JSON.stringify(
      [{ number: 318, title: 'T-0100: the finished one', merged_at: '2026-09-02T00:00:00Z', created_at: '2026-09-01T00:00:00Z' }]));
    const { status, out } = landed(APP);
    check('11. it reports nothing, and exits 0', status === 0 && /nothing/i.test(out), out.split('\n')[0]);
    check('    …and refuses to call that a clean bill of health',
      /absence is silence, not proof/.test(out), out.trim());
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

/* ------------------------ 12: an unreachable API degrades to silence, not to an
   accusation. The transports are `gh` and `curl`; PATH is emptied so neither
   resolves, which is the same answer a run offline gets. */

{
  const { tmp, APP } = sandbox();
  try {
    console.log('\n  no network and no transport at all — the live path, not the fixture');
    const r = spawnSync(process.execPath, [path.join(APP, 'tools', 'ticket.mjs'), 'landed'],
      { cwd: APP, encoding: 'utf8', env: { ...process.env, PATH: path.join(tmp, 'nothing'), GITHUB_TOKEN: '', GH_TOKEN: '' } });
    const out = `${r.stdout ?? ''}${r.stderr ?? ''}`;
    check('12. an unreachable API exits 0', r.status === 0, `exit ${r.status}`);
    check('    …and reports NOTHING rather than accusing anything',
      !/T-0429/.test(out), out.trim().slice(0, 200));
    check('    …and says why its silence is not evidence',
      /not evidence/.test(out), out.trim().slice(0, 200));
  } finally { rmSync(tmp, { recursive: true, force: true }); }
}

console.log(`\n${failures === 0 ? 'ticket landed self-test: all pass' : `ticket landed self-test: ${failures} FAILURE(S)`}`);
process.exit(failures === 0 ? 0 : 1);
