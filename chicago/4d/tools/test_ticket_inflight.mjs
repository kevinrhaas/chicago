#!/usr/bin/env node
/**
 * test_ticket_inflight.mjs — `ticket.mjs inflight` reports a claim that outlived the
 * three-hour window, and still refuses to call a finished branch work.
 *
 * WHY THIS EXISTS (T-0852). `inflight` read branch AGE and nothing else. A run claims,
 * pushes its claim commit, and then READS sources for four hours; at the three-hour
 * mark its branch fell out of the hot list and into one headed "finished tickets, or
 * branches older than a run" — both halves of which are false about it. It dropped out
 * at exactly the moment duplicating it was most expensive. Cohort 14 (T-0509) was read
 * twice on 2026-09-05 by two runs that could not see each other; the ledgers disagreed
 * on 36 of the 76 people and T-0816 had to adjudicate every one.
 *
 * WHY IT TAKES TWO WITNESSES AND NOT ONE. The obvious fix — trust the ticket file, and
 * call any `claimed` ticket's branch live however old — was written first and measured
 * against the real remote, where it reported SEVEN long-merged branches of T-0987 as in
 * flight. That ticket is worked one stretch per run and sits `claimed` on `dev`
 * permanently by design. So the file is necessary and not sufficient, and the second
 * witness is the CLAIM LOCK: `claim/t-nnnn` is taken in the same breath as the claim and
 * released by `ticket.mjs done`, so it lives exactly as long as the run does. Case 3
 * below is T-0987's shape and it is the reason the lock is in the rule.
 *
 * AND WHY `held` IS NOT `live`. T-0802's blind spot runs the other way: a run that dies
 * between its merge and `ticket.mjs done` leaves a ticket `claimed` behind a genuinely
 * cold branch. T-0429 sat that way for five days as the topmost queue line carrying no
 * PR — the exact shape of available work — and a run rebuilt 116 files onto records
 * already on `dev`. A third reading keeps both faults visible at once: `held` is printed
 * under IN FLIGHT with its age and a line saying a claim outliving a run is either a long
 * read or a dead one, and that the PR list decides which.
 *
 * WHY THE TEST IS A FIXTURE. The correct answer against the real remote changes by the
 * hour, so it cannot be the demonstration. `inflight --branches-json` reads a CONSTRUCTED
 * branch list ([{ name, age_hours }]) — the same device `landed --pr-json` uses, for the
 * same reason — and `--json` prints the reading each branch got. No network is reachable
 * from any case here, which is the point: this command stands between a run and its work
 * and must never be able to stop one.
 *
 * AND WHY A FIXTURE CAN BE TOO KIND (T-1427). Cases 14-18 pass a constructed PR list, and
 * for three days they passed over a guard that could not work at all: `restGet` projected a
 * pull request down to four fields, `head.ref` not among them, while the fixture rows here
 * carried `head.ref` by hand. The fixture was richer than production and the gate reported
 * on the fixture. Both now go through `normalizePull`, so a row written in GitHub's own
 * shape is read exactly as GitHub's answer is read, and case 23 says the one thing no
 * fixture can reach — that the fetch asks for open pull requests at all.
 *
 * The sandbox is test_ticket_landed.mjs's: ticket.mjs resolves its paths from its own
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

const TICKETS = [
  ['T-0509', 'The cohort a run claimed and then read for four hours', 'claimed'],
  ['T-0987', 'The recurring ticket that is claimed on dev permanently by design', 'claimed'],
  ['T-0429', 'The ticket whose run died between its merge and `done`', 'claimed'],
  ['T-1105', 'The ticket a run picked up eight minutes ago', 'open'],
  ['T-0042', 'The near miss a number match invites', 'claimed'],
  ['T-0055', 'The old branch on a ticket nobody ever claimed', 'open'],
  ['T-0100', 'The ticket that is finished', 'done'],
  ['T-0266', 'The ticket whose branch tip this clone does not hold', 'open'],
  ['T-0662', 'The ticket a run put up for review and is still on', 'review'],
  ['T-0800', 'The ticket whose branch did get a pull request, and it was closed', 'open'],
  ['T-0900', 'The ticket whose branch is up for review right now, and parked on hold', 'open'],
];

// name, age_hours. `null` = the object is not in this clone and the age is unknowable.
const BRANCHES = [
  // 1. the base case: a run that pushed eight minutes ago.
  { name: 'steward/t-1105-tract-aware-generators', age_hours: 0.13 },
  // 2. THE FAULT. Five hours of reading, and the claim lock still stands.
  { name: 'steward/t-0509-cohort-14', age_hours: 5 },
  { name: 'claim/t-0509', age_hours: 5 },
  // 3. T-0987's shape: claimed on dev forever, lock long since released by `done`.
  { name: 'steward/t-0987-stretch-10-norris', age_hours: 40 },
  { name: 'steward/t-0987-stretch-11-hidden-surnames', age_hours: 12 },
  // 4. T-0429's shape: the run died after the merge, and `done` had let the lock go.
  { name: 'steward/t-0429-south-water-lasalle', age_hours: 120 },
  // 5. an old branch on a ticket nobody claimed — cold, exactly as before.
  { name: 'steward/t-0055-kinzie-view-plate-source', age_hours: 30 },
  // 6. a finished ticket is cold however young its branch, and however stray its lock.
  { name: 'steward/t-0100-the-finished-one', age_hours: 0.5 },
  { name: 'claim/t-0100', age_hours: 0.5 },
  // 7. the claim marker on its own, before the run's first push.
  { name: 'claim/t-0662', age_hours: 6 },
  { name: 'steward/t-0662-mint-labels', age_hours: 6 },
  // 8. a tip this clone does not hold: age unknowable.
  { name: 'steward/t-0266-phone-picket-moire', age_hours: null },
  // 11. the near miss: T-0042's lock must not travel to T-0429.
  { name: 'claim/t-0042', age_hours: 9 },
  // 14. T-1155's shape twice over: two old branches on unfinished tickets with no
  // lock. Offline they are indistinguishable, and the PR list separates them —
  // T-0800's PR was opened and closed, T-0055's never existed.
  { name: 'steward/t-0800-had-a-pr', age_hours: 50 },
  // 19. T-1427's shape: an OPEN pull request on a branch older than a run. Every age
  // reading here calls it cold; the PR list is the only thing that knows better.
  { name: 'steward/t-0900-north-corridors', age_hours: 10 },
];

function sandbox() {
  const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-inflight-'));
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
  writeFileSync(path.join(APP, 'branches.json'), JSON.stringify(BRANCHES, null, 2));
  return { tmp, APP };
}

function inflight(APP, file = 'branches.json', ...extra) {
  const r = spawnSync('node',
    [path.join(APP, 'tools', 'ticket.mjs'), 'inflight', '--branches-json', path.join(APP, file), ...extra],
    { cwd: APP, encoding: 'utf8' });
  return { status: r.status, out: `${r.stdout ?? ''}${r.stderr ?? ''}` };
}

/* ---------------------------------------------------- 1-11: the constructed list */

{
  const { tmp, APP } = sandbox();
  try {
    console.log('\n  a constructed branch list, no network, ticket.mjs inflight');
    const { status, out } = inflight(APP);
    const json = inflight(APP, 'branches.json', '--json');
    const rows = JSON.parse(/\[[\s\S]*\]\s*$/.exec(json.out)?.[0] ?? 'null') ?? [];
    const read = (branch) => rows.find((r) => r.branch === branch)?.reading;
    // The line a branch is printed on, so "reported in flight" is asserted against the
    // rendered report and not only against the JSON the report is built from.
    const lines = out.split('\n');
    const coldFrom = lines.findIndex((l) => /^Cold —/.test(l));
    const printedCold = (branch) => coldFrom >= 0 && lines.slice(coldFrom).some((l) => l.includes(branch));
    const printedInFlight = (branch) =>
      lines.slice(0, coldFrom < 0 ? lines.length : coldFrom).some((l) => l.includes(branch));

    check('1. a branch pushed minutes ago on an open ticket is live',
      read('steward/t-1105-tract-aware-generators') === 'live');

    check('2. THE FAULT: a 5h branch whose claim still stands is reported in flight',
      read('steward/t-0509-cohort-14') === 'held'
      && printedInFlight('steward/t-0509-cohort-14')
      && !printedCold('steward/t-0509-cohort-14'),
      read('steward/t-0509-cohort-14'));
    check('   …with its age shown, and named as a claim that outlived a run',
      /steward\/t-0509-cohort-14.*5h ago/.test(out) && /claim still stands on the remote/.test(out));
    check('   …and the run\'s own claim marker is in flight beside it',
      read('claim/t-0509') === 'held');

    check('3. T-0987: a ticket claimed on dev by design, whose lock was released, stays cold',
      read('steward/t-0987-stretch-10-norris') === 'cold'
      && read('steward/t-0987-stretch-11-hidden-surnames') === 'cold'
      && printedCold('steward/t-0987-stretch-10-norris'),
      read('steward/t-0987-stretch-10-norris'));

    check('4. T-0429: the run that died after its merge is cold, not resurrected as work',
      read('steward/t-0429-south-water-lasalle') === 'cold');

    check('5. an old branch on a ticket nobody claimed is cold, as it always was',
      read('steward/t-0055-kinzie-view-plate-source') === 'cold');

    check('6. a done ticket is cold however young the branch, and however stray the lock',
      read('steward/t-0100-the-finished-one') === 'cold' && read('claim/t-0100') === 'cold');

    check('7. `review` is held on the same footing as `claimed`',
      read('claim/t-0662') === 'held' && read('steward/t-0662-mint-labels') === 'held');

    check('8. an unknowable age is live, never cold — a blip may not invent litter',
      read('steward/t-0266-phone-picket-moire') === 'live');

    check('9. the cold heading no longer calls a held branch finished or litter',
      /^Cold — finished tickets, or unclaimed branches older than a run/m.test(out));

    check('10. the IN FLIGHT count is every live and held branch, and no cold one',
      new RegExp(`IN FLIGHT — ${rows.filter((r) => r.reading !== 'cold').length} branch`).test(out),
      out.split('\n')[0]);

    check('11. a near miss: T-0042\'s claim lock does not make T-0429 held',
      read('claim/t-0042') === 'held' && read('steward/t-0429-south-water-lasalle') === 'cold');

    check('12. it exits 0 and reports; it is a report, not a gate', status === 0, `status ${status}`);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

/* ------------------------------------------- 13: nothing readable is not a finding */

{
  const { tmp, APP } = sandbox();
  try {
    console.log('\n  an unreachable remote');
    writeFileSync(path.join(APP, 'empty.json'), '[]');
    const { status, out } = inflight(APP, 'empty.json');
    check('13. an empty branch list says so and accuses nobody',
      status === 0 && /nothing to report/.test(out) && !/IN FLIGHT — \d/.test(out), out.trim());
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

/* ------------- 14-18: `recoverable` — work on the remote that nobody can see */

/**
 * T-1155, 2026-09-17. A run claimed the ticket, wrote the whole fix, pushed it, and was
 * CANCELLED at its timeout cap before opening a pull request. Salvage pushed the branch,
 * so the work was complete and on the remote; every instrument here called it litter.
 * The claim went stale at three hours, a second run stole it and rebuilt the same 71-file
 * fix. `cold` covered two different animals, and only the PR list tells them apart:
 *
 *   T-0429's shape — a merged PR names the ticket. The work LANDED; the branch is litter.
 *   T-0055's shape — no merged PR, and no PR ever carried the branch. The work is LOST.
 *
 * So these cases hold both against one constructed PR list, and hold the refusal too: with
 * no answer from the PR list, nothing is upgraded, because an empty answer is not evidence.
 */
const PULLS = [
  // T-0429's work landed. Its branch is litter, exactly as case 4 says.
  { number: 597, title: 'T-0429: deepen the south water at LaSalle',
    merged_at: '2026-09-01T00:40:50Z', created_at: '2026-08-31T00:00:00Z',
    head: { ref: 'steward/t-0429-south-water-lasalle' } },
  // T-0800's PR was opened and CLOSED UNMERGED. The work did not land — but it was never
  // invisible either, and this reading is only for work nobody can see.
  { number: 1251, title: 'T-0800: the one that was closed', merged_at: null,
    created_at: '2026-09-12T00:00:00Z', head: { ref: 'steward/t-0800-had-a-pr' } },
  // T-0987 SHIPPED ITS STRETCHES, and this row is why the case is here. The ticket is
  // `claimed` on dev permanently by design, so its long-merged branches have exactly the
  // shape this reading hunts for — old, unfinished, unlocked — and calling them lost would
  // reintroduce the loudness the lock was added to cure (case 3). The PR list is what
  // saves it: one merged PR naming the ticket accounts for every branch that carries it.
  { number: 1200, title: 'T-0987: stretch 10, the Norris surnames',
    merged_at: '2026-09-08T00:00:00Z', created_at: '2026-09-07T00:00:00Z',
    head: { ref: 'steward/t-0987-stretch-10-norris' } },
  // T-1427, and the row is written in GITHUB'S OWN SHAPE — `state`, `labels` as objects
  // with a `name`, `head.ref` — because the fixture and the API now arrive through one
  // projection (`normalizePull`). That is the point of the case as much as the reading
  // is: when the projection dropped `head.ref`, the fixture supplied it by hand and the
  // gate stayed green over a guard that was dead in production.
  { number: 1533, title: 'T-0900: the corridor layer reaches the north bank',
    state: 'open', merged_at: null, created_at: '2026-09-19T18:38:40Z',
    labels: [{ name: 'hold' }],
    head: { ref: 'steward/t-0900-north-corridors' } },
];

{
  const { tmp, APP } = sandbox();
  try {
    console.log('\n  the same branches, held against a constructed PR list');
    writeFileSync(path.join(APP, 'pulls.json'), JSON.stringify(PULLS, null, 2));
    const { status, out } = inflight(APP, 'branches.json', '--pr-json', path.join(APP, 'pulls.json'));
    const json = inflight(APP, 'branches.json', '--pr-json', path.join(APP, 'pulls.json'), '--json');
    const rows = JSON.parse(/\[[\s\S]*\]\s*$/.exec(json.out)?.[0] ?? 'null') ?? [];
    const read = (branch) => rows.find((r) => r.branch === branch)?.reading;

    check('14. THE FAULT: an old branch on an unfinished ticket that no merged PR names',
      read('steward/t-0055-kinzie-view-plate-source') === 'recoverable',
      read('steward/t-0055-kinzie-view-plate-source'));
    check('   …is printed under RECOVERABLE with the compare URL that opens its PR',
      /RECOVERABLE — 1 branch\(es\) carrying work NOBODY CAN SEE/.test(out)
      && /compare\/dev\.\.\.steward\/t-0055-kinzie-view-plate-source\?expand=1/.test(out));

    check('15. T-0429 stays cold: a merged PR names it, so the branch really is litter',
      read('steward/t-0429-south-water-lasalle') === 'cold',
      read('steward/t-0429-south-water-lasalle'));

    check('16. a branch whose PR was opened and closed is cold — it was never invisible',
      read('steward/t-0800-had-a-pr') === 'cold', read('steward/t-0800-had-a-pr'));

    check('17. a claim marker is a lock, never recoverable work',
      rows.filter((r) => r.branch.startsWith('claim/') && r.reading === 'recoverable').length === 0);

    check('   …and live and held readings are untouched by any of it',
      read('steward/t-1105-tract-aware-generators') === 'live'
      && read('steward/t-0509-cohort-14') === 'held');

    check('17b. T-0987, claimed on dev by design: its merged stretches stay litter, both of',
      read('steward/t-0987-stretch-10-norris') === 'cold'
      && read('steward/t-0987-stretch-11-hidden-surnames') === 'cold',
      'one PR naming the ticket accounts for every branch carrying it');

    // ---------------------------------------------- 19-22: the OPEN pull request
    //
    // T-1427, 2026-09-20. `inflight` printed `steward/t-1191-north-corridors` under
    // "carrying work NOBODY CAN SEE ... no PR ever carried this branch" while PR #1533
    // was open on that exact branch and labelled `hold` — parked for the owner on
    // purpose, its gate not green. The one reading that exists to stop a duplicate
    // rebuild was pointing a run at the owner's parked work and telling it to rebuild.
    const openLines = out.split('\n');
    const sectionFrom = (re) => {
      const i = openLines.findIndex((l) => re.test(l));
      if (i < 0) return [];
      const j = openLines.findIndex((l, k) => k > i && /^[A-Z][A-Za-z ]+ — /.test(l));
      return openLines.slice(i, j < 0 ? openLines.length : j);
    };
    check('19. THE FAULT: a branch with an OPEN pull request is not "work nobody can see"',
      read('steward/t-0900-north-corridors') === 'open_pr',
      read('steward/t-0900-north-corridors'));
    check('   …it is printed with its PR number, under a heading of its own',
      /OPEN PULL REQUESTS — 1 branch\(es\) whose work is already up for review/.test(out)
      && sectionFrom(/^OPEN PULL REQUESTS —/).some((l) => /PR #1533 is OPEN/.test(l)));
    check('20. a `hold` label is said out loud: parked for the owner, do not rebuild it',
      sectionFrom(/^OPEN PULL REQUESTS —/).some((l) => /labelled hold/.test(l))
      && /PARKED it for the owner on purpose/.test(out));
    check('21. and it is in NEITHER list that would have a run overwrite or delete it',
      !sectionFrom(/^RECOVERABLE —/).some((l) => l.includes('steward/t-0900-north-corridors'))
      && !sectionFrom(/^Cold —/).some((l) => l.includes('steward/t-0900-north-corridors')),
      'the cold list\'s standing advice is `git push origin --delete <branch>`');
    check('22. the RECOVERABLE reading still finds the branch that really is invisible',
      read('steward/t-0055-kinzie-view-plate-source') === 'recoverable'
      && /RECOVERABLE — 1 branch\(es\)/.test(out),
      'one open PR must not swallow the reading it sits beside');
    check('   …and --json carries the PR number for a caller that is not reading prose',
      rows.find((r) => r.branch === 'steward/t-0900-north-corridors')?.open_pr === 1533
      && rows.find((r) => r.branch === 'steward/t-0055-kinzie-view-plate-source')?.open_pr === null);

    check('   …and it still exits 0', status === 0, `status ${status}`);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

{
  const { tmp, APP } = sandbox();
  try {
    console.log('\n  …and with no answer from the PR list');
    const noPr = inflight(APP, 'branches.json', '--json');
    const rows = JSON.parse(/\[[\s\S]*\]\s*$/.exec(noPr.out)?.[0] ?? 'null') ?? [];
    check('18. without the PR list nothing is called recoverable — silence is not evidence',
      rows.every((r) => r.reading !== 'recoverable')
      && rows.find((r) => r.branch === 'steward/t-0055-kinzie-view-plate-source')?.reading === 'cold',
      'the fixture run must reach no network at all');
    const skipped = inflight(APP, 'branches.json', '--no-landed', '--json');
    const rows2 = JSON.parse(/\[[\s\S]*\]\s*$/.exec(skipped.out)?.[0] ?? 'null') ?? [];
    check('   …and --no-landed says the same, without asking', rows2.every((r) => r.reading !== 'recoverable'));
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

/* ------------------------------- 23: the one assertion no fixture can carry */

/**
 * THE HALF OF T-1427 THAT LIVES IN THE FETCH. Every case above runs on a constructed
 * PR list, which is what makes them stable — and it is also why none of them can see
 * the query string. `closedPulls` asked GitHub for `state=closed`, so an open pull
 * request was never in the collection at all and a perfectly repaired classifier would
 * still have called #1533 invisible. A fixture cannot fail on that; only the source can
 * say it, so this says it, and says plainly that it is reading the source and not the
 * behaviour.
 */
{
  console.log('\n  the query the fixtures cannot reach');
  const src = readFileSync(path.join(REPO, 'tools', 'ticket.mjs'), 'utf8');
  const q = /repos\/kevinrhaas\/custom\/pulls\?state=(\w+)/.exec(src)?.[1] ?? null;
  check('23. the PR fetch asks for open pull requests as well as closed ones',
    q === 'all', `the query asks state=${q} (read from the source, not from a run)`);
}

console.log(failures ? `\n  ${failures} failure(s)\n` : '\n  inflight reads a long claim as work, a merged branch as litter, an unseen branch as recoverable, and a branch under review as neither\n');
process.exit(failures ? 1 : 0);
