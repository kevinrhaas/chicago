#!/usr/bin/env node
/**
 * The ticket queue's one tool: create, claim, close, block, list, board, check.
 *
 * WHY THIS EXISTS. On 2026-08-17 the owner reported that his own requests were
 * untraceable — "i asked for a whole list of items … it's hard to find that
 * list anywhere in your files" — while the loop researched what it preferred.
 * The operational state ("what next, what's in flight, what's blocked on whom")
 * lived inside an 11,407-line ROADMAP.md and a 6,838-line STATUS.md, which no
 * owner can reorder and no agent can hold in context. Tickets pull the STATE
 * out; the prose stays where it is, as archive.
 *
 * DESIGN RULES, each bought by a documented failure in this repo:
 *  - One file per ticket. Two branches that edit one shared list corrupt it —
 *    the changelog's union-merge history is seven repairs long.
 *  - State lives ONLY in front matter. No state directories: a file's location
 *    and its `state:` field would be two copies of one fact, and this project's
 *    recurring fault is exactly two copies of one fact disagreeing.
 *  - BOARD.md and tickets.json are GENERATED, and since T-0937 they are also
 *    UNTRACKED (.gitignore). `check` and `board` WRITE them rather than refusing a
 *    stale one: a build product that no commit carries cannot be stale, and it
 *    cannot conflict either, which is the whole point — a run's first act is
 *    `claim`, so these three files were rewritten by every branch before it had
 *    done any work, and GitHub's merge runs no driver to reconcile them (T-0857).
 *  - IDs are assigned here, not guessed by authors — two branches that each
 *    guess "top + 1" both get it wrong (the v93/v98 collisions). `nextIdNum`
 *    counts merged tickets AND every branch still in flight on the remote, over
 *    ALL origin refs — narrowing that scan to `steward/*` is what let T-0672 be
 *    minted twice on 2026-09-04, from a `claude/*` branch it could not see. Two
 *    branches created in the same instant can still collide; `check` catches it
 *    at merge and `restamp` is the remedy.
 *  - QUEUE.md order belongs to the owner. This tool APPENDS on `new`, REMOVES
 *    on `done`/`block`/`withdraw`, and never reorders. `check` asserts the
 *    queue is exactly the workable-open set, so it cannot silently drift from
 *    the tickets, but the ORDER of its lines is never touched by machinery.
 *
 * The front-matter parser is deliberately not YAML: flat `key: value` lines
 * between two `---` fences, values read as string | null | true | false. What
 * tickets/README.md documents is exactly what parses; nothing else does.
 */
import { readFileSync, writeFileSync, readdirSync, existsSync, renameSync } from 'node:fs';
import { execFileSync, spawnSync } from 'node:child_process';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT = path.resolve(HERE, '..');
const DIR = path.join(ROOT, 'tickets');
const QUEUE = path.join(DIR, 'QUEUE.md');
const BOARD = path.join(DIR, 'BOARD.md');
const JSON_OUT = path.join(DIR, 'tickets.json');

/**
 * THE PUBLISHED MIRROR OF tickets.json — T-0154, and it is here because the two
 * rules that govern a closing PR could not both be obeyed in the order AGENTS.md
 * states them.
 *
 *   1. do the work, run `tools/publish.sh` — "PUBLISH IN THE SAME COMMIT";
 *   2. push, open the PR — the PR NUMBER does not exist until this moment;
 *   3. `ticket.mjs done T-NNNN --pr N` — "close it in the merging PR";
 *   4. …which rewrites tickets.json, and `check_published.mjs` compares that file
 *      to this mirror byte for byte. The gate is now red, on every close.
 *
 * Step 3 needs a number that only step 2 can produce, so no ordering of the
 * documented steps ends green. What actually happened instead was a REMEMBERED
 * extra `publish.sh` after the close — the unwritten step that goes wrong at 3am,
 * and did on T-0153/PR #318.
 *
 * So the writer of the file maintains its mirror. Deliberately narrow:
 *  - it copies when this tool actually rewrote tickets.json, OR when the mirror is
 *    ABSENT. Not on every invocation: a mirror that somebody else made stale must
 *    still fail the gate — the acceptance clause says so in as many words — and a
 *    blanket refresh would quietly launder exactly that. The absent case is T-0937
 *    and it does not weaken anything, because an absent file is not a stale one:
 *    both this file and its mirror are untracked now, so a fresh clone starts with
 *    NEITHER, and "only on a rewrite" would leave the mirror missing on any clone
 *    that happened to rebuild the source first.
 *  - it never creates the mirror directory. An unpublished checkout stays
 *    unpublished; `publish.sh` is what decides the mirror exists.
 *  - `check` pins the copy line in publish.sh, below, so the destination cannot
 *    drift into two disagreeing copies of one fact.
 */
const MIRROR = path.resolve(ROOT, '../../site/chicago/4d/tickets.json');
/** The line in publish.sh this mirror is the twin of. `check` asserts it survives. */
const PUBLISH_SH = path.join(ROOT, 'tools/publish.sh');
const PUBLISH_PIN = 'cp -f tickets/tickets.json "$SITE/tickets.json"';

/** The day the ledger began stamping the finishing instant. Tickets closed on or
 *  after it must carry `closed_at`; everything older is left as it was recorded. */
const CLOSED_AT_SINCE = '2026-09-04';

/** This repository on GitHub — the board links its PRs, and `inflight` its pulls page. */
const REPO_URL = 'https://github.com/kevinrhaas/custom';

const STATES = ['open', 'claimed', 'review', 'done', 'blocked-owner', 'blocked-tech',
  'withdrawn', 'split'];
/**
 * EFFORT IS MEASURED IN RUNS, NOT IN POINTS.
 *
 * The owner asked on 2026-08-17 whether tickets should carry work points and be
 * split past a threshold. Points are a proxy; the thing they proxy for here is
 * concrete and already binding — **can ONE run take this from claim to a merged,
 * gated, visibly-changed dev?** A run has hard edges in this project: a ~150-min
 * budget, a 10-minute per-command ceiling that the desktop smoke does not fit
 * inside, and the bake boundary (no Blender on the improve runner). So the unit
 * is the run, and the test is the acceptance clause: **if a ticket needs more
 * than one demonstration to be done, it is more than one ticket.**
 *
 * The evidence it was needed: on its first run under this queue the loop took
 * T-0001 (walkable bridges), shipped only the walker-deck half, titled the PR
 * "T-0001(1/2)" and left the ticket `claimed` — it had to invent a notation
 * because the system could not say "this is two runs".
 */
const EFFORT = {
  XS: 'part of a run',
  S: 'one run',
  M: 'one run, tight — or one run plus a bake',
  L: 'MORE THAN ONE RUN — must be split before it can be claimed',
};
// PAPERS: the newspaper-corpus epic — extraction from the 1833-1835 Democrat
// and American transcriptions, and the documented businesses/residents seeded
// from them. Registered 2026-08-28 with the epic's nine founding tickets
// (T-0256..T-0264), on the owner's instruction.
const EPICS = ['RENDERING', 'TOWN', 'GROUND', 'FLORA', 'PIPELINE', 'META', 'PAPERS', 'SOUTH_TIME'];
const BY = ['owner', 'loop', 'steward'];
// Workable = an agent may take it off the queue. `claimed`/`review` stay in the
// queue so a crashed run's ticket is still visible in priority order rather
// than vanishing into a state nobody lists.
const WORKABLE = ['open', 'claimed', 'review'];

/* ---------------------------------------------------------------- parsing */

function parseTicket(file) {
  const src = readFileSync(file, 'utf8');
  const m = /^---\n([\s\S]*?)\n---\n?/.exec(src);
  if (!m) return { file, error: 'no front-matter fence' };
  const t = { file, body: src.slice(m[0].length) };
  for (const line of m[1].split('\n')) {
    if (!line.trim()) continue;
    const kv = /^([a-z_]+):\s*(.*)$/.exec(line);
    if (!kv) return { file, error: `unparseable front-matter line: "${line}"` };
    const v = kv[2].trim();
    t[kv[1]] = v === 'null' ? null : v === 'true' ? true : v === 'false' ? false : v;
  }
  return t;
}

function loadAll() {
  if (!existsSync(DIR)) return [];
  return readdirSync(DIR)
    .filter((f) => /^T-\d{4}.*\.md$/.test(f))
    .map((f) => parseTicket(path.join(DIR, f)));
}

function writeTicket(t) {
  const keys = ['id', 'title', 'state', 'epic', 'requested_by', 'seen', 'effort',
    'legacy_id', 'parent', 'opened', 'closed', 'pr', 'claimed_by', 'blocked_on', 'needs_bake',
    // Appended, never inserted: a ticket file written by an older checkout is
    // still valid, and these two are read as null when absent.
    'closed_at', 'claimed_run'];
  const fm = keys.map((k) => `${k}: ${t[k] ?? 'null'}`).join('\n');
  writeFileSync(t.file, `---\n${fm}\n---\n${t.body ?? ''}`);
}

function today() {
  // Central Time, the project's clock (AGENTS.md).
  return new Date().toLocaleDateString('en-CA', { timeZone: 'America/Chicago' });
}

/** The instant, in UTC. `closed` is the Central Time DAY a ticket finished, which
 *  is what a person reads; `closed_at` is the instant, which is what an ordering
 *  needs. Two tickets closed on the same day were closed in an order, and before
 *  this existed the board had to fall back on ticket id — so the newest work
 *  read as if it had been done alphabetically. */
function nowIso() { return new Date().toISOString(); }

/** The project's clock, spelled the way the board and the changelog spell it. */
function ctFmt(d) {
  return new Date(d).toLocaleString('en-US', { timeZone: 'America/Chicago',
    month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' });
}

/** The Actions run that is executing this command, when there is one. A steward
 *  run's Bash calls inherit the step environment, so a claim made by the loop can
 *  say WHICH run holds the ticket — the thing `claimed_by`'s timestamp could never
 *  answer. A claim made by hand gets null, honestly. */
function runUrl() {
  const { GITHUB_SERVER_URL: server, GITHUB_REPOSITORY: repo, GITHUB_RUN_ID: id } = process.env;
  return server && repo && id ? `${server}/${repo}/actions/runs/${id}` : null;
}

function slugOf(title) {
  return title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48);
}

const git = (args) => execFileSync('git', args, {
  cwd: ROOT, encoding: 'utf8', timeout: 20_000, stdio: ['ignore', 'pipe', 'ignore'],
});

/** The branch this checkout is on, or '' when detached or there is no git. */
function currentBranch() {
  try { return git(['rev-parse', '--abbrev-ref', 'HEAD']).trim(); } catch { return ''; }
}

/**
 * Every branch head on the remote, read ONCE per process — `inflight` asks about
 * a hundred tickets and one `ls-remote` answers all of them. `main` and `dev` are
 * never work-in-progress, so they never appear.
 *
 * Failure returns [] on purpose: these callers stand between a run and its work,
 * and a network blip must never be able to stop one.
 */
let branchCache = null;
function remoteBranches() {
  if (branchCache) return branchCache;
  try {
    branchCache = git(['ls-remote', '--heads', 'origin'])
      .split('\n')
      .map((l) => {
        const [sha, ref] = l.split('\t');
        return { name: ref?.split('refs/heads/')[1]?.trim(), sha: sha?.trim() };
      })
      .filter((b) => b.name && b.name !== 'main' && b.name !== 'dev');
  } catch {
    branchCache = [];
  }
  return branchCache;
}

/**
 * THE HIGHEST TICKET NUMBER ANYWHERE — this tree, plus every ticket sitting on a
 * branch that has not merged yet.
 *
 * Ids used to be `max + 1` over the LOCAL tickets directory, which only ever holds
 * what has merged. Two branches opened the same afternoon therefore both computed
 * the same next number, and `check` refused the second one at the merge. That
 * happened THREE TIMES in two days (T-0084, T-0111, T-0116), and each time the
 * repair cost a rebase — and, until `restamp` was fixed alongside this, the
 * renumbered ticket also lost its place in the owner's queue.
 *
 * So look where the in-flight numbers actually are: the tickets directory of every
 * `steward/*` branch on the remote. One `ls-tree` per branch, no checkout, no
 * fetch of file contents — the FILENAMES carry the ids.
 *
 * Best-effort, like everything else here that touches the network: no git, no
 * remote, or a stale clone just means the old local-only answer, never a refusal
 * to create a ticket. It narrows the window; `check` still closes it.
 */
function remoteIdMax() {
  try {
    // Refresh the steward refs so a branch pushed minutes ago is visible. Cheap:
    // these branches are a few commits off dev and share nearly all their objects.
    try {
      git(['fetch', '--quiet', '--prune', 'origin', '+refs/heads/*:refs/remotes/origin/*']);
    } catch { /* offline, or no such refspec — fall through to whatever is cached */ }
    // EVERY origin ref, not just `steward/*`. This scanned `refs/remotes/origin/steward`
    // alone until 2026-09-04, which left two holes that both bit on the same day:
    //
    //   - `origin/dev` ITSELF was never read. A clone whose local tickets/ is behind dev
    //     — any branch cut before a merge landed — would take its own stale local max.
    //   - The fleet has more than one branch convention. Web sessions push `claude/*`;
    //     T-0672 was minted twice in one afternoon because PR #765 held it on
    //     `claude/research-output-data-updates-cst1d5`, which this scan could not see.
    //     `agent/*` exists too. A prefix allowlist is a bug waiting for the next prefix.
    //
    // Measured before widening it, because the whole point is that this runs on every
    // `new`: 410 refs scanned in 1.4 s, 499 in 1.6 s, and the incremental fetch is if
    // anything faster unfiltered. The old narrowness bought nothing.
    const refs = git(['for-each-ref', '--format=%(refname)', 'refs/remotes/origin'])
      .split('\n').map((s) => s.trim()).filter(Boolean);
    // `<ref>:<path>` resolves against the CWD, not the top of the tree — from
    // `chicago/4d` a path of `chicago/4d/tickets` silently reads as
    // `chicago/4d/chicago/4d/tickets` and returns EMPTY WITH EXIT 0, which is how
    // this scan first shipped finding nothing at all and quietly handing back the
    // old local-only answer. So ask git where the top is and read from there.
    const top = git(['rev-parse', '--show-toplevel']).trim();
    const dir = `${git(['rev-parse', '--show-prefix']).trim()}tickets`;
    let max = 0;
    for (const ref of refs) {
      let names = '';
      try {
        names = execFileSync('git', ['ls-tree', '--name-only', `${ref}:${dir}`], {
          cwd: top, encoding: 'utf8', timeout: 20_000, stdio: ['ignore', 'pipe', 'ignore'],
        });
      } catch { continue; }        // a branch from before the queue existed
      for (const m of names.matchAll(/^T-(\d{4})-/gm)) max = Math.max(max, Number(m[1]));
    }
    return max;
  } catch {
    return 0;
  }
}

/** The next free id, counting merged tickets AND every branch still in flight. */
function nextIdNum(tickets) {
  const local = Math.max(0, ...tickets.map((t) => Number(/^T-(\d{4})$/.exec(t.id ?? '')?.[1] ?? 0)));
  return Math.max(local, remoteIdMax()) + 1;
}

const idOf = (n) => `T-${String(n).padStart(4, '0')}`;

/**
 * How many hours since this branch was last pushed to, or null if unknowable.
 *
 * NOT ancestry. Everything here squash-merges, so a merged branch's head is never
 * an ancestor of `dev` and `merge-base --is-ancestor` answers "unmerged" for every
 * branch that ever landed — a confidently wrong signal, which is worse than none.
 * Age is the honest one: a steward run lasts under two hours, so a branch whose tip
 * is a day old is not a run at work, whatever its ticket says.
 *
 * Reads the commit only if it is already in this clone (it is, for anything fetched);
 * no network, and null when the object is absent.
 */
function branchAgeHours(sha) {
  if (!sha) return null;
  try {
    const ts = Number(git(['log', '-1', '--format=%ct', sha]).trim());
    return Number.isFinite(ts) ? (Date.now() / 1000 - ts) / 3600 : null;
  } catch {
    return null;
  }
}

/** A run lasts ~1 hour; nothing older than this is one, whatever else is true. */
const RUN_HOURS = 3;

/**
 * IS SOMEBODY ON THIS BRANCH RIGHT NOW? — `live` / `held` / `cold` (T-0852).
 *
 * Branch AGE was the whole answer until now, and it has a blind spot the lane pays
 * for. A run claims, pushes its claim commit, and then READS for four hours; at the
 * three-hour mark its branch drops out of the hot list and `inflight` files it under
 * "finished tickets, or branches older than a run". Both halves of that heading are
 * false about it — it is neither finished nor litter — and it drops out at exactly
 * the moment duplicating it is most expensive. Cohort 14 (T-0509) was read twice on
 * 2026-09-05 by two runs that could not see each other; the two ledgers disagreed on
 * 36 of the 76 people and T-0816 had to adjudicate every one of them.
 *
 * So age is no longer the only witness. TWO others answer together, and it takes
 * both — the first draft of this took only the ticket file and was too loud to use:
 *
 *   - the ticket FILE says `claimed` or `review`. Necessary, not sufficient. T-0987
 *     is worked one stretch per run and is `claimed` on `dev` permanently by design,
 *     so the file alone reported all SEVEN of its long-merged branches as in flight.
 *   - a CLAIM LOCK for that ticket stands on the remote. `claim/t-nnnn` is taken in
 *     the same breath as the claim and released by `ticket.mjs done`, so it is alive
 *     for exactly as long as the run is — however many hours that run spends reading.
 *     It costs nothing to ask: `remoteBranches` already lists every head, this one
 *     included, in the one `ls-remote` this command was already making.
 *
 * `held` rather than `live`, and the distinction is the honest part. T-0802's blind
 * spot runs the other way: a run that dies between its merge and `ticket.mjs done`
 * leaves the ticket `claimed` behind a genuinely cold branch — T-0429 sat that way
 * for five days and cost a 116-file rebuild. If an old claim simply became `live`
 * this command would hide that one forever. `held` reports the branch as in flight,
 * prints its age, and says in one line that a claim outliving a run is either a long
 * read or a dead one and the PR list decides which. `cold` keeps exactly the meaning
 * it always had.
 *
 * Offline, and deliberately: `landed` is where the PR question is asked, and these
 * callers stand between a run and its work.
 */
/**
 * AND A FOURTH READING, `recoverable`, WHICH THIS FUNCTION DELIBERATELY CANNOT GIVE.
 *
 * T-1155, 2026-09-17. A steward run claimed the ticket, wrote the whole fix, pushed it,
 * and was CANCELLED at its timeout cap before it opened a pull request. Salvage pushed
 * the branch, so the work was on the remote and complete; nothing else knew. The claim
 * lock went stale at three hours, a second run stole it, and rebuilt the same 71-file
 * fix from scratch. Held against the three readings above, that branch is `cold` — an
 * unclaimed branch older than a run — which is the heading that says "finished, or
 * litter". It was neither, and it is the second time this exact sentence has had to be
 * written (see T-0429 above, whose branch really was litter).
 *
 * The two cases are IDENTICAL offline: unfinished ticket, old branch, no lock. What
 * separates them is whether the work already landed, and only the PR list knows that.
 * So `recoverable` is decided in the `inflight` command, where `collectLanded` has just
 * answered, and never here — this function stays offline, pure, and unable to stop a
 * run that has no network.
 */
const HELD_STATES = ['claimed', 'review'];
function inflightState(state, ageHours, locked = false) {
  if (['done', 'withdrawn', 'split'].includes(state)) return 'cold';
  if (ageHours === null || ageHours <= RUN_HOURS) return 'live';
  return locked && HELD_STATES.includes(state) ? 'held' : 'cold';
}

/** Which tickets have a claim marker standing on the remote, out of one branch list. */
function lockedIds(branches) {
  const held = new Set();
  for (const b of branches) {
    if (!isClaimMarker(b.name)) continue;
    const n = /t-?0*(\d+)/i.exec(b.name)?.[1];
    if (n) held.add(idOf(Number(n)));
  }
  return held;
}

/** How old, in the words the reports use. */
const ageWords = (h) => (h === null ? '' : h < 1 ? `${Math.round(h * 60)}m ago` : `${Math.round(h)}h ago`);

/**
 * Does this branch name carry this ticket's number?
 *
 * Branch names are not standardised — the same ticket has been worked on
 * `steward/t62-more-docks` and `steward/t-0062-more-docks` — so match the NUMBER
 * with its padding and its separator optional, and refuse to match a longer one
 * (T-0062 must not fire on `t-0620`).
 */
function branchCarries(branch, id) {
  const n = /^T-(\d+)$/.exec(id)?.[1];
  if (!n) return false;
  return new RegExp(`(?:^|[^0-9a-z])t-?0*${Number(n)}(?![0-9])`, 'i').test(branch);
}

/** A claim marker is not a work branch — see the claim lock below. */
const isClaimMarker = (name) => /^claim\//.test(name);

/** Branches that look like somebody ELSE is already working this ticket.
 *  Claim markers are deliberately NOT counted here: the lock is the authority on
 *  a live claim and says who holds it and since when, so letting them fall
 *  through to this scan would only replace a precise message with a vague one. */
function remoteBranchesFor(id, state = 'open') {
  const here = currentBranch();
  return remoteBranches()
    .filter((b) => b.name !== here && !isClaimMarker(b.name) && branchCarries(b.name, id))
    .map((b) => {
      const age = branchAgeHours(b.sha);
      // The same three-way reading `inflight` uses, so the two commands cannot
      // disagree about the same branch. Before T-0852 this said "likely litter"
      // about every branch past the window — including the one belonging to a run
      // still reading sources on a ticket the files themselves call `claimed`.
      switch (inflightState(state, age, lockedIds(remoteBranches()).has(id))) {
        case 'held':
          return `${b.name}  (last pushed ${ageWords(age)}, and ${id}'s claim still stands on the remote — a long read or a dead run; the PR list decides)`;
        case 'cold':
          return `${b.name}  (last pushed ${ageWords(age)} — older than a run, likely litter)`;
        default:
          return b.name;
      }
    });
}

/* --------------------------------------------- did its PR already merge? (T-0802)

 * THE BLIND SPOT `inflight` IS HONEST ABOUT. Everything here squash-merges, so a
 * merged branch never becomes an ancestor of `dev` and git cannot be asked whether
 * work landed. `inflight` therefore sorts on branch AGE, and a ticket whose run died
 * between the merge and `ticket.mjs done` stays `claimed` with a COLD branch — which
 * reads as litter, not as done, and `claimed` with no PR is exactly the shape of
 * available work.
 *
 * T-0429 is the instance and it is costed. Its PR #597 merged to `dev` on
 * 2026-09-01T00:40:50Z; the run died before closing the ticket; five days later it was
 * still the topmost queue line carrying no PR, and `steward/t-0429-south-water-lasalle`
 * rebuilt the whole block — 116 files, 5,827 insertions, baked — on records that
 * already existed on `dev` under the same ids. tickets/README.md costs a recurrence at
 * about seventy minutes of loop time.
 *
 * The question that settles it is cheap and it is the same evidence a person uses:
 * for each ticket not in a terminal state, does a MERGED pull request name its id?
 *
 * THREE RULES, AND EACH IS A REFUSAL TO OVERREACH.
 *
 *  1. IT REPORTS, IT NEVER FAILS. The id in a PR title is a convention, not a
 *     contract. A gate that hard-fails on a naming convention blocks a run that did
 *     nothing wrong, so `landed` exits 0 with findings and check.sh does not call the
 *     network at all — what the gate runs is the offline self-test.
 *  2. EVIDENCE ONE WAY ONLY. A merged PR naming T-NNNN is strong evidence the work
 *     landed. Its ABSENCE proves nothing — a PR whose title omits its id is invisible
 *     here — so silence is never reported as a clean bill of health.
 *  3. NO NETWORK DEGRADES TO SILENCE, NEVER TO A FALSE ACCUSATION. `remoteBranches`
 *     is the precedent: these callers stand between a run and its work, and a blip
 *     must not be able to stop one, nor to invent a finding out of an empty answer.
 */

/**
 * WHICH TICKETS ARE ASKED ABOUT, and it is WORKABLE — not simply "not terminal".
 *
 * The harm is precise: a finished ticket left in the states that OFFER it as work.
 * `open`/`claimed`/`review` are exactly those states (they are what QUEUE.md and
 * `list --workable` carry), and T-0429 sat in one of them for five days looking
 * like the next thing to do.
 *
 * `blocked-owner` and `blocked-tech` are deliberately excluded even though they are
 * not terminal. A run BLOCKS a ticket in the merging PR, the same way it closes one
 * — so every blocked ticket in the repository is named by a merged PR, by design.
 * Reporting those would be a permanent false-positive class, and rule 3 says the
 * check does not get to manufacture findings. They are not offered as work either,
 * which is the harm this exists to stop.
 */
const asksAbout = (t) => WORKABLE.includes(t.state);

/**
 * The ids a PR TITLE claims to be the work of — read from the title's LEADING id run
 * ONLY, and that anchoring is the whole precision of this check.
 *
 * The convention in this repo is `T-NNNN: sentence`, or `T-0867/T-0868: sentence` when
 * one PR closes two. Everything else a title does with an id is ABOUT the ticket
 * rather than the work of it, and the first draft of this function — which matched an
 * id anywhere in the title's first clause — reported all three kinds as landed:
 *
 *   "Rank T-0727 under the drain band, and restore the band the queue driver stripped"
 *   "Pull T-0802 up into the blocking band, on the evidence that caught it"
 *   "File T-0968: a green deploy is not proof the site is reachable"
 *
 * Three queue-keeping PRs, three tickets that had not been touched, three accusations.
 * Prose after the colon is the same trap in the other direction — "T-0995: the shared
 * roll lines T-0992's spend leaves unsaid" is not a claim about T-0992. So the id must
 * START the title, and only ids joined to it by a separator a multi-ticket title uses
 * come with it. That is rule 3 enforced in a regex: a check that must never accuse
 * falsely reads the one position the convention actually reserves.
 */
function prTicketIds(title) {
  const out = [];
  let rest = String(title ?? '').trim();
  for (;;) {
    const m = /^T-?0*(\d{1,4})\b/i.exec(rest);
    if (!m) break;
    out.push(idOf(Number(m[1])));
    rest = rest.slice(m[0].length);
    const sep = /^\s*(?:[/,&+]|and\b)\s*/i.exec(rest);
    if (!sep) break;
    rest = rest.slice(sep[0].length);
  }
  return [...new Set(out)];
}

/**
 * A pull request cut down to the fields the joins actually read — six pages of whole
 * PR objects is tens of megabytes held for no reason.
 *
 * IT IS A NAMED FUNCTION AND NOT AN INLINE `.map` BECAUSE THE FIXTURES MUST GO THROUGH
 * IT TOO (T-1427). The projection used to drop `head.ref`, and `inflight`'s
 * "a branch that ever HAD a pull request was never invisible" guard reads exactly that
 * field — so against the live API the guard was an empty set and could never fire,
 * while `test_ticket_inflight.mjs` supplied `head.ref` in its own fixture rows and the
 * gate went green. A check dead in production and green in the gate is worse than no
 * check, and the cure is that the fixture and the API arrive by one road.
 *
 * `labels` is flattened to names, which is how `inflight` says `hold` out loud.
 */
function normalizePull(p) {
  return {
    number: p?.number, title: p?.title,
    state: p?.state ?? null,
    merged_at: p?.merged_at ?? null, created_at: p?.created_at ?? null,
    labels: Array.isArray(p?.labels)
      ? p.labels.map((l) => (typeof l === 'string' ? l : l?.name)).filter(Boolean) : [],
    head: { ref: p?.head?.ref ?? null },
  };
}

/** A REST GET that returns parsed JSON, or null — `gh api` if the runner has it
 *  authenticated, else plain `curl`. Both synchronous, both time-boxed, both silent
 *  on failure. REST only: the GraphQL bucket is a separate hourly quota the fleet
 *  exhausts, and `gh pr`/`gh issue` spend it. */
function restGet(pathAndQuery) {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
  const attempts = [
    ['gh', ['api', '-H', 'Accept: application/vnd.github+json', pathAndQuery]],
    ['curl', ['-sS', '--max-time', '25', '-H', 'Accept: application/vnd.github+json',
      ...(token ? ['-H', `Authorization: Bearer ${token}`] : []),
      `https://api.github.com/${pathAndQuery}`]],
  ];
  for (const [bin, argv] of attempts) {
    // maxBuffer is EXPLICIT and large because the default is 1 MB and a page of a
    // hundred pull requests is several: spawnSync answers ENOBUFS, which arrives
    // here indistinguishable from "no network" and made the very first run of this
    // check report a false silence.
    const r = spawnSync(bin, argv, { encoding: 'utf8', timeout: 30_000, maxBuffer: 64 * 1024 * 1024 });
    if (r.error || r.status !== 0 || !r.stdout) continue;
    try {
      const body = JSON.parse(r.stdout);
      // A rate-limit answer is a well-formed OBJECT, not the array we asked for.
      // Treating it as zero results would report "nothing landed" from a refusal.
      if (!Array.isArray(body)) continue;
      return body.map(normalizePull);
    } catch { /* not JSON — try the next transport */ }
  }
  return null;
}

/**
 * Pull requests, OPEN AND CLOSED, newest-created first, far enough back to cover the
 * oldest ticket we are asking about.
 *
 * It asked for `state=closed` until T-1427, and the open half is the half that stops a
 * run from rebuilding work: PR #1533 was open on `steward/t-1191-north-corridors` and
 * deliberately labelled `hold`, and `inflight` — unable to see it — printed the branch
 * under "carrying work NOBODY CAN SEE ... no PR ever carried this branch". The reading
 * that exists to prevent a duplicate rebuild was inviting one, at the owner's own parked
 * work. `landedFindings` filters on `merged_at`, so the merged-PR reconciliation is
 * unchanged by the wider ask.
 *
 * Paging is bounded two ways: it stops once a page's oldest `created_at` predates
 * every ticket in question (no PR can name a ticket that did not exist yet), and it
 * stops at `maxPages` regardless. The horizon it reached is REPORTED, because a
 * ticket older than the horizon is one this check did not actually cover, and rule 2
 * says we do not get to call that clean.
 */
function recentPulls({ since = null, maxPages = 6, perPage = 100 } = {}) {
  const pulls = [];
  let pages = 0;
  let horizon = null;
  for (let page = 1; page <= maxPages; page += 1) {
    const batch = restGet(`repos/kevinrhaas/custom/pulls?state=all&sort=created`
      + `&direction=desc&per_page=${perPage}&page=${page}`);
    if (batch === null) return { ok: pages > 0, pulls, pages, horizon, truncated: true };
    pages += 1;
    pulls.push(...batch);
    const oldest = batch.map((p) => p.created_at).filter(Boolean).sort()[0] ?? null;
    if (oldest && (!horizon || oldest < horizon)) horizon = oldest;
    if (batch.length < perPage) return { ok: true, pulls, pages, horizon, truncated: false };
    if (since && horizon && horizon < since) return { ok: true, pulls, pages, horizon, truncated: false };
  }
  return { ok: true, pulls, pages, horizon, truncated: true };
}

/**
 * The join, and it is a pure function of (tickets, pulls) so that the gate can run it
 * on a constructed case with no network — which is the only honest way to demonstrate
 * a check whose correct answer against today's `dev` is "nothing".
 */
function landedFindings(tickets, pulls) {
  const merged = (pulls ?? []).filter((p) => p && p.merged_at);
  const byId = new Map();
  for (const p of merged) {
    for (const id of prTicketIds(p.title)) {
      const prev = byId.get(id);
      // The EARLIEST merge is the one that landed the work; later ones are follow-ups.
      if (!prev || String(p.merged_at) < String(prev.merged_at)) byId.set(id, p);
    }
  }
  return tickets
    .filter((t) => t.id && asksAbout(t) && byId.has(t.id))
    .map((t) => ({ t, pr: byId.get(t.id) }))
    .sort((a, b) => String(a.pr.merged_at).localeCompare(String(b.pr.merged_at)));
}

/** How far back the read actually reached — a ticket opened before the horizon was
 *  NOT covered, and rule 2 forbids calling that clean. */
function coverage(fetched, since) {
  if (fetched.pages === 0) return 'Read from a fixture, not from the API.';
  const day = (s) => String(s ?? '').slice(0, 10);
  const reach = fetched.horizon
    ? `back to ${day(fetched.horizon)}` : 'over an unknown range';
  const gap = fetched.truncated && since && fetched.horizon && day(fetched.horizon) > day(since)
    ? ` — which does NOT reach the oldest workable ticket (opened ${day(since)}), so anything older than the horizon is simply unexamined`
    : '';
  return `Read ${fetched.pages} page(s) of pull requests (open and closed), ${reach}${gap}.`;
}

/** Prints the report. Returns nothing and throws nothing: every caller is a run on
 *  its way to work, and this is the last thing that should be able to stop one. */
/**
 * THE PR QUESTION, ASKED ONCE AND ANSWERED AS DATA (not printed).
 *
 * `inflight` needs this answer BEFORE it prints, because a branch whose ticket no
 * merged PR names is a different animal from one whose work is already on `dev` —
 * see `recoverable` below. `reportLanded` then prints from the same collection
 * rather than asking GitHub twice.
 *
 * `ok` is the load-bearing field and it is NOT the same as an empty `found`: rule 2
 * of this command is that an empty answer from the API is never evidence, so a caller
 * that cannot tell must say so rather than conclude anything.
 */
function collectLanded(tickets, { fixture = null, maxPages = 6 } = {}) {
  const asked = tickets.filter((t) => t.id && asksAbout(t));
  const since = asked.map((t) => t.opened).filter(Boolean).sort()[0] ?? null;
  const fetched = fixture
    ? { ok: true, pulls: fixture.map(normalizePull), pages: 0, horizon: null, truncated: false }
    : recentPulls({ since, maxPages });
  return {
    ok: fetched.ok,
    found: fetched.ok ? landedFindings(asked, fetched.pulls) : [],
    pulls: fetched.ok ? (fetched.pulls ?? []) : [],
    fetched, since, asked,
  };
}

function reportLanded(tickets, { quiet = false, fixture = null, maxPages = 6, collected = null } = {}) {
  const gathered = collected ?? collectLanded(tickets, { fixture, maxPages });
  const { found, fetched, since, asked } = gathered;

  if (!fetched.ok) {
    if (!quiet) {
      console.log('MERGED-PR RECONCILIATION — no answer from the API (offline, unauthenticated,');
      console.log('or rate-limited). Reporting nothing: an empty answer is not evidence that');
      console.log('every claimed ticket is still unfinished.\n');
    }
    return gathered;
  }

  if (!found.length) {
    if (!quiet) {
      console.log(`MERGED-PR RECONCILIATION — nothing. None of the ${asked.length} workable `
        + `ticket(s) is named by a merged PR.`);
      console.log('That is not a clean bill of health: a PR whose title omits its id is');
      console.log('invisible here, so absence is silence, not proof.');
      console.log(coverage(fetched, since) + '\n');
    }
    return gathered;
  }

  console.log(`MERGED-PR RECONCILIATION — ${found.length} unfinished ticket(s) named by a MERGED PR:\n`);
  for (const { t, pr } of found) {
    console.log(`  ${t.id}  ${String(t.state).padEnd(9)} ${t.requested_by === 'owner' ? 'OWNER ' : '      '}${t.title}`);
    console.log(`          ↳ PR #${pr.number} merged ${pr.merged_at} — ${JSON.stringify(String(pr.title).slice(0, 90))}`);
    console.log(`          if that work is on dev, close it: node tools/ticket.mjs done ${t.id} --pr ${pr.number}\n`);
  }
  console.log('This REPORTS and never fails a gate. The id in a PR title is a convention,');
  console.log('not a contract, so a naming coincidence must not be able to stop a run —');
  console.log('read the PR before you close the ticket on it.');
  console.log(coverage(fetched, since) + '\n');
  return gathered;
}

/* ------------------------------------------------------- the claim lock */

/**
 * THE CLAIM IS A LOCK ON THE REMOTE, AND IT IS TAKEN AT CLAIM TIME.
 *
 * WHY THIS EXISTS (owner, 2026-09-11, asking "can you prevent duplicate claiming
 * going forward?" after six open PRs turned out to be six runs working tickets
 * another run had already finished — T-0990, T-1008, T-0867/T-0868, T-1026,
 * T-0424, T-1011, every one of them closed on `dev` by somebody else).
 *
 * `claim` writes `state: claimed` into a ticket FILE, and that file reaches `dev`
 * only when the PR merges — so until then every other run reads the ticket as
 * `open`. `remoteBranchesFor` above is the mitigation and it is the right idea,
 * but it can only see a branch that has been PUSHED, and a run does not push for
 * about an hour after it claims. Measured on the two duplicates that cost most:
 *
 *   T-1026  winner claimed 03:46, loser claimed 04:10 — 24 minutes later — and
 *           the winner's branch was not pushed until 05:27. A 1h41m window with
 *           nothing on the remote to see.
 *   T-1008  the LOSER claimed FIRST, at 18:05. The run that won claimed at 19:08,
 *           read `dev`, and saw `open`, because the first claim was still local.
 *           Claiming earlier is no protection at all when claims are invisible.
 *
 * So a claim now takes a marker ref on the remote BEFORE any work, and the push
 * that takes it is a compare-and-swap the SERVER decides: `--force-with-lease=
 * <ref>:` with an empty expected value means "only if this ref does not exist".
 * Two runs claiming in the same second cannot both win. Verified against a real
 * remote before this was written, all four cases — create, reject, steal, and a
 * steal with the wrong expected sha.
 *
 * IT IS STILL NEVER A FALSE STOP, which is the property the branch scan already
 * promised. A REJECTION refuses the claim. Anything else — no network, no
 * credentials, no remote, a checkout with no push rights — warns and lets the run
 * through, exactly as a failed `ls-remote` does.
 *
 * A marker older than RUN_HOURS is a run that died, and is STOLEN automatically:
 * the steal leases on the sha the marker actually holds, so two runs racing to
 * steal one dead claim still produce exactly one winner. That is why a crashed
 * run cannot strand a ticket — the worst it costs is RUN_HOURS.
 *
 * The marker is a branch (`claim/t-1026`) rather than a ref under some private
 * namespace, for two reasons: GitHub accepts pushes to `refs/heads/*` without
 * argument, and `branchCarries` already matches it, so `inflight` and the rival
 * scan see claims for free. It is a PARENTLESS, EMPTY-TREE commit — it carries no
 * code, cannot be merged into anything by accident, and its commit date is the
 * honest age of the claim. The janitor sweeps `steward/*`, never `claim/*`.
 */
const claimBranch = (id) => `claim/${id.toLowerCase()}`;

/** git that REPORTS failure instead of throwing, and keeps stderr — the lock
 *  has to tell a rejection from an unreachable remote, and that is in stderr. */
function gitTry(args) {
  const r = spawnSync('git', args, {
    cwd: ROOT,
    encoding: 'utf8',
    timeout: 30_000,
    // The identity is forced rather than assumed. `commit-tree` dies with
    // `fatal: empty ident name` on a runner that never configured one, and that
    // is not hypothetical — it is the bug that silently broke every PR lap until
    // 2026-09-10 (.github/steward/pr-lap.sh). A tool that only writes an orphan
    // marker should never be the thing that needs a configured git user.
    // `||`, NOT `??`, and the test holds it there: git refuses an EMPTY ident
    // (`fatal: empty ident name (for <>) not allowed`) exactly as it refuses an
    // absent one, and `??` passes an empty string straight through. Caught by
    // test_ticket_claim_lock case 7, which reported a claim that succeeded and
    // wrote no marker — the lock silently doing nothing, which is worse than
    // refusing, because the run believes it holds the ticket.
    env: {
      ...process.env,
      GIT_AUTHOR_NAME: process.env.GIT_AUTHOR_NAME || 'polecat-steward',
      GIT_AUTHOR_EMAIL: process.env.GIT_AUTHOR_EMAIL || 'steward@polecat.live',
      GIT_COMMITTER_NAME: process.env.GIT_COMMITTER_NAME || 'polecat-steward',
      GIT_COMMITTER_EMAIL: process.env.GIT_COMMITTER_EMAIL || 'steward@polecat.live',
    },
  });
  return {
    ok: r.status === 0,
    out: (r.stdout ?? '').trim(),
    err: `${r.stderr ?? ''}${r.error ? ` ${r.error.message}` : ''}`.trim(),
  };
}

/**
 * Did this push fail because the remote ALREADY HOLDS the ref, or because we
 * could not reach the remote at all? Only the first is an answer about the
 * ticket; the second must never stop a run.
 */
const isRefRejection = (err) =>
  /\[rejected\]|stale info|non-fast-forward|fetch first|cannot lock ref|already exists/i.test(err);

/**
 * The claim record itself: one parentless commit, empty tree, message = who.
 *
 * THE NONCE IS LOad-BEARING, and it is the whole lock. A commit object is a pure
 * function of its content, so two runs building a parentless empty-tree commit
 * with the same forced identity, the same message and the same SECOND produce
 * the SAME SHA — and git answers the second one `Everything up-to-date`, exit 0.
 * The loser is then told it won, which is precisely the simultaneous claim this
 * lock exists to decide. Found by test_ticket_claim_lock, whose two runs claim
 * inside one second; it is not exotic, because two slices of one workflow share
 * `runUrl()` as well as the clock.
 */
function claimCommit(id, by, run) {
  const tree = gitTry(['hash-object', '-w', '-t', 'tree', '/dev/null']);
  if (!tree.ok || !tree.out) return null;
  const nonce = `${Date.now().toString(36)}${process.pid.toString(36)}${Math.random().toString(36).slice(2, 10)}`;
  const msg = `claim ${id} — ${by}${run ? `\n\nrun: ${run}` : ''}\nnonce: ${nonce}`;
  const c = gitTry(['commit-tree', tree.out, '-m', msg]);
  return c.ok && c.out ? c.out : null;
}

/** Who holds the marker for this ticket, and since when. */
function inspectClaim(id) {
  const ref = `refs/heads/${claimBranch(id)}`;
  const ls = gitTry(['ls-remote', 'origin', ref]);
  const sha = ls.ok ? (ls.out.split('\t')[0] || '').trim() : '';
  if (!sha) return { sha: null, by: null, ageHours: null };
  // The object is one commit with an empty tree; fetching it is cheap, and it is
  // the only way to read a claim's AGE and its run URL without the web API.
  gitTry(['fetch', '--quiet', 'origin', ref]);
  const log = gitTry(['log', '-1', '--format=%ct%n%B', sha]);
  if (!log.ok) return { sha, by: null, ageHours: null };
  const [ts, ...rest] = log.out.split('\n');
  const ageHours = Number.isFinite(Number(ts)) ? (Date.now() / 1000 - Number(ts)) / 3600 : null;
  return { sha, ageHours, by: rest.join('\n').trim() || null };
}

const sinceWords = (h) =>
  h === null ? 'age unknown'
    : h < 1 ? `taken ${Math.max(1, Math.round(h * 60))}m ago`
      : `taken ${h.toFixed(1)}h ago`;

/**
 * Take the claim for `id`. Returns one of:
 *   { held: true }                      this run holds it
 *   { held: false, ... }                somebody else does — refuse
 *   { unknown: why }                    the remote could not answer — proceed
 */
function takeClaimLock(id, by, run, { steal = false } = {}) {
  const ref = `refs/heads/${claimBranch(id)}`;
  const commit = claimCommit(id, by, run);
  if (!commit) return { unknown: 'could not write a claim commit' };

  const take = (expect) =>
    gitTry(['push', 'origin', `${commit}:${ref}`, `--force-with-lease=${ref}:${expect}`]);

  let push = take('');                       // '' — the ref must not exist
  // A push that changed NOTHING never took anything, whatever its exit status.
  // With the nonce above this is unreachable; it is kept because the failure it
  // guards is silent, and a silent lock is worse than no lock at all.
  if (push.ok && /Everything up-to-date/i.test(push.err)) {
    return { unknown: 'the claim push changed nothing' };
  }
  if (push.ok) return { held: true };
  if (!isRefRejection(push.err)) {
    return { unknown: (push.err.split('\n').filter(Boolean).pop() || 'push failed').trim() };
  }

  const holder = inspectClaim(id);
  const dead = holder.ageHours !== null && holder.ageHours > RUN_HOURS;
  if (!steal && !dead) return { held: false, ...holder };
  if (!holder.sha) return { held: false, ...holder };

  // Stealing leases on the sha the marker ACTUALLY holds, so two runs racing to
  // steal one dead claim still produce exactly one winner.
  push = take(holder.sha);
  return push.ok ? { held: true, stolen: holder } : { held: false, ...holder, raced: true };
}

/** Give the claim back. Best-effort by design: a marker nobody released is
 *  litter, never a block, because a stale one is stolen on the next claim.
 *
 *  Best-effort is not the same as SILENT, which is what this was. Every caller
 *  ignores the boolean, so a delete that failed looked exactly like one that
 *  worked — and three `done` tickets carried a marker for days with nothing
 *  anywhere saying so. A missing ref is the one failure that is not news: it
 *  means the marker was already gone, which is the state we wanted. */
function releaseClaimLock(id) {
  const r = gitTry(['push', 'origin', '--delete', claimBranch(id)]);
  const alreadyGone = /remote ref does not exist|unable to delete/i.test(r.err || '');
  if (!r.ok && !alreadyGone) {
    const why = (r.err || '').trim().split('\n').filter(Boolean).pop() || 'no reason given';
    console.warn(`  NOTE: the claim marker ${claimBranch(id)} was not released — ${why}\n`
      + `        That is litter, not a block: a marker older than ${RUN_HOURS}h is stolen by the\n`
      + `        next claim, and \`ticket.mjs claims --sweep\` clears it.`);
  }
  return r.ok;
}

// ---------------------------------------------------------------------------
// T-1287. AN ID IS RESERVED ON THE REMOTE BEFORE IT IS USED, NOT SCANNED FOR.
//
// `nextIdNum` reads the highest id on every origin ref and adds one. That scan
// works — measured 2026-09-18, 1,066 refs in 8 s, and it correctly reports ids
// sitting on other runs' branches. It is still not enough, and the reason is not
// that it misses anything:
//
//   A MINTED ID IS INVISIBLE TO EVERY OTHER RUN UNTIL THE BRANCH IS PUSHED.
//
// Measured the same day. This session renumbered a ticket to T-1324 and pushed
// twenty minutes later; #1455 minted AND MERGED its own T-1324 inside that
// window. No scan could have seen the first — it existed only on one disk. Five
// collisions that day, and the fifth was created by a careful attempt to dodge
// the fourth by picking an id above everything visible. "Above everything
// visible" is read-then-write, and any run minting in between wins the race.
//
// So minting takes a lock, exactly as claiming a ticket does (T-1145's marker
// branches, which are a real compare-and-swap and have held since). Push an
// empty commit to `refs/heads/idlock/t-NNNN` with a lease saying THE REF MUST
// NOT EXIST; git rejects the loser atomically, and the loser tries the next
// number. Two runs minting in the same second get different ids, whatever either
// of them can see.
//
// OFFLINE STILL MINTS. A sandbox with no remote, and the test suite, must be able
// to file a ticket — so an unreachable origin falls back to the scan with a
// warning that says exactly what was given up. A REJECTION is different from an
// unreachable remote and is never treated as one.
const idLockBranch = (id) => `idlock/${id.toLowerCase()}`;

function reserveIdNum(startAt, count = 1) {
  const taken = [];
  let n = startAt;
  let attempts = 0;
  while (taken.length < count && attempts < 40) {
    attempts += 1;
    const id = idOf(n);
    const ref = `refs/heads/${idLockBranch(id)}`;
    const commit = claimCommit(id, 'mint', null);
    if (!commit) { return { ids: null, why: 'could not write a lock commit' }; }
    const push = gitTry(['push', 'origin', `${commit}:${ref}`, `--force-with-lease=${ref}:`]);
    // A PUSH THAT CHANGED NOTHING NEVER RESERVED ANYTHING, whatever its exit status —
    // the same guard `takeClaimLock` carries, and for a worse failure. Two runs that
    // build a parentless empty-tree commit with the same forced identity in the same
    // second produce the SAME SHA, and git answers the second `Everything up-to-date`,
    // exit 0. `claimCommit`'s nonce should make that unreachable; the guard stays
    // because if it ever is reached the loser is told it holds an id another run holds
    // too, which is exactly the collision this whole mechanism exists to stop.
    if (push.ok && /Everything up-to-date/i.test(push.err || '')) {
      return { ids: null, why: 'the reservation push changed nothing' };
    }
    if (push.ok) { taken.push(id); n += 1; continue; }
    if (isRefRejection(push.err)) { n += 1; continue; }   // somebody holds it — step past
    return { ids: null, why: (push.err || '').trim().split('\n').filter(Boolean).pop() || 'push failed' };
  }
  if (taken.length < count) return { ids: null, why: `no free id found in ${attempts} attempts` };
  return { ids: taken };
}

/**
 * `count` consecutive-ish ids, reserved on the remote where another run can see
 * them. Falls back to the local+remote scan when the remote cannot be reached,
 * and says so, because a mint that fails is worse than a mint that races.
 */
function mintIds(tickets, count = 1) {
  const start = nextIdNum(tickets);
  const got = reserveIdNum(start, count);
  if (got.ids) return got.ids;
  console.warn(`  NOTE: the id lock could not be taken — ${got.why}.`);
  console.warn('        Falling back to the highest id this clone can SEE, which is a race:');
  console.warn('        another run minting right now cannot see this id until the branch is');
  console.warn('        pushed, and may take it too (T-1287). Push early if you can.');
  return Array.from({ length: count }, (_, i) => idOf(start + i));
}

function find(tickets, id) {
  const t = tickets.find((x) => x.id === id);
  if (!t) { console.error(`no ticket ${id}`); process.exit(1); }
  return t;
}

function queueIds() {
  return queueLines().map(queueId).filter(Boolean);
}

function queueAppend(t) {
  const cur = existsSync(QUEUE) ? readFileSync(QUEUE, 'utf8').replace(/\n+$/, '\n') : queueHeader();
  writeFileSync(QUEUE, cur + `${t.id} — ${t.title}\n`);
}

// PLACE BESIDE THE WORK IT SERVES (owner, 2026-09-10). A run that files what it finds
// at the foot of the queue leaves it there: by 2026-09-10 the file had reached 195
// lines, and the bottom third was findings filed under the ticket that found them and
// never worked. `new --after T-NNNN` puts the new line directly under the ticket it
// grew out of, INSIDE that ticket's band, so the queue's shape survives a run.
//
// This is placement, not re-ranking: it inserts one line at a position an existing
// ticket already defines, and it never moves a line the owner placed. Returns false
// when the anchor is not in the queue (closed, blocked, or a typo), and the caller
// then appends and says so — a quiet fallback would put the line somewhere the run
// did not choose and the owner cannot see.
function queueInsertAfter(t, afterId) {
  const lines = queueLines();
  const at = lines.findIndex((l) => queueId(l) === afterId);
  if (at < 0) return false;
  lines.splice(at + 1, 0, `${t.id} — ${t.title}`);
  writeFileSync(QUEUE, lines.join('\n').replace(/\n+$/, '\n'));
  return true;
}

function queueLines() {
  if (!existsSync(QUEUE)) return [];
  return readFileSync(QUEUE, 'utf8').split('\n');
}

/** The id a queue line carries, or null for a comment/blank/prose line. */
function queueId(line) {
  return /^(T-\d{4})\b/.exec(line.trim())?.[1] ?? null;
}

/**
 * The LABEL half of a queue line — everything after the id, which QUEUE.md's own
 * header calls "a label, not data" and which is regenerated from the ticket's
 * `title:`. It is also the only thing that tells two lines carrying the SAME id
 * apart, which is what `queueIndexOf` below needs it for.
 */
function queueLabel(line) {
  return /^T-\d{4}\s*[—-]\s*(.*)$/.exec(line.trim())?.[1]?.trim() ?? '';
}

/**
 * THE LINE THAT BELONGS TO ONE PARTICULAR TICKET — by id AND by label (T-0217).
 *
 * Matching on the id alone is right in every state `check` allows, and wrong in
 * the one state `restamp` exists to repair: a duplicate id puts TWO lines in the
 * queue carrying it, and `indexOf` returns whichever the owner happened to rank
 * higher — a coin toss. On 2026-08-27 it came up tails during T-0215's merge and
 * silently overwrote a queue line the owner had ordered with another ticket's
 * title, leaving a stale line behind for good measure. `check` was green
 * throughout; it was caught by reading `tail QUEUE.md`.
 *
 * The title is the discriminator because the line was WRITTEN from it. When it
 * cannot discriminate — a hand-edited label, or genuinely identical titles — this
 * falls back to the first line carrying the id, i.e. the old behaviour, and the
 * caller says out loud that it guessed. A repair tool that refused to run would
 * leave the duplicate in place, which is worse.
 */
function queueIndexOf(id, title) {
  const lines = queueLines();
  const carries = (l) => queueId(l) === id;
  const exact = lines.findIndex((l) => carries(l) && queueLabel(l) === title);
  return { i: exact >= 0 ? exact : lines.findIndex(carries), byLabel: exact >= 0 };
}

function queueReplaceAt(i, rows) {
  // Children take the PARENT'S EXACT PLACE in the order. Appending them to the
  // bottom would silently demote work the owner had deliberately ranked — the
  // one thing this file's ordering rule exists to prevent. A split is a
  // clarification of what the work is, never a re-prioritisation of it.
  const lines = queueLines();
  if (i < 0) lines.push(...rows); else lines.splice(i, 1, ...rows);
  writeFileSync(QUEUE, lines.join('\n').replace(/\n+$/, '\n'));
}

function queueReplace(id, rows, title) {
  queueReplaceAt(queueIndexOf(id, title).i, rows);
}

function queueRemove(id) {
  if (!existsSync(QUEUE)) return;
  const kept = readFileSync(QUEUE, 'utf8').split('\n')
    .filter((l) => !l.trim().startsWith(id)).join('\n');
  writeFileSync(QUEUE, kept.replace(/\n+$/, '\n'));
}

function queueHeader() {
  return `# QUEUE — top is next. THE OWNER ORDERS THIS FILE; agents only append and remove.\n`
    + `# Reorder by moving lines. Everything after the ticket id on a line is a label, not data.\n\n`;
}

/* ----------------------------------------------------------------- board */

function generateBoard(tickets) {
  const at = ctFmt(new Date());
  const order = queueIds();
  const rank = (t) => { const i = order.indexOf(t.id); return i < 0 ? 9999 : i; };
  const sec = (name, list, line) => list.length
    ? `## ${name} (${list.length})\n\n${list.map(line).join('\n')}\n\n` : '';
  const row = (t) => `- **${t.id}** ${t.title}`
    + `${t.requested_by === 'owner' ? ' · **OWNER**' : ''}`
    + `${t.seen === true ? ' · SEEN' : ''}${t.needs_bake === true ? ' · needs-bake' : ''}`
    + `${t.legacy_id ? ` · was ${t.legacy_id}` : ''}`
    + `${t.state === 'claimed' || t.state === 'review' ? ` · ${t.state}` : ''}`;
  const open = tickets.filter((t) => WORKABLE.includes(t.state)).sort((a, b) => rank(a) - rank(b));
  const owner = tickets.filter((t) => t.state === 'blocked-owner');
  const tech = tickets.filter((t) => t.state === 'blocked-tech');
  const split = tickets.filter((t) => t.state === 'split');
  const working = tickets.filter((t) => t.state === 'claimed' || t.state === 'review')
    .sort((a, b) => rank(a) - rank(b));

  // FINISH ORDER, and it has to survive two eras of ticket. `closed` is the
  // Central Time DAY, which every done ticket has; `closed_at` is the instant,
  // which only tickets closed since 2026-09-03 have. So: day first, then the
  // instant inside that day, then the PR number — which rises with time and is
  // the only ordering the 300-odd older tickets carry. The ticket id is the last
  // resort and never the first, because sorting finished work alphabetically is
  // exactly the thing this section exists to stop doing.
  const byFinish = (a, b) => String(b.closed ?? '').localeCompare(String(a.closed ?? ''))
    || String(b.closed_at ?? '').localeCompare(String(a.closed_at ?? ''))
    || (Number(b.pr) || 0) - (Number(a.pr) || 0)
    || String(b.id).localeCompare(String(a.id));
  const finished = tickets.filter((t) => t.state === 'done').sort(byFinish);
  const shown = finished.slice(0, 100);

  const md = `# BOARD — generated by \`tools/ticket.mjs board\`, ${at} CT. Do not edit.\n\n`
    + sec('Claimed — being worked now', working, (t) => `${row(t)}`
      + `${t.claimed_by ? ` · ${t.claimed_by}` : ''}`
      + `${t.claimed_run ? ` · [the run](${t.claimed_run})` : ''}`)
    + sec('In the queue, in the owner’s order', open, row)
    + sec('⏸ Waiting on an owner decision', owner, (t) => `${row(t)}\n  - **the question:** ${t.blocked_on}`)
    + sec('Blocked on tooling or another ticket', tech, (t) => `${row(t)} — ${t.blocked_on}`)
    + sec('Split into pieces (the pieces are in the queue)', split, (t) => `${row(t)}`
      + ` — ${tickets.filter((c) => c.parent === t.id).map((c) => c.id).join(', ')}`)
    + sec(`Finished, newest first${finished.length > shown.length
      ? ` — ${shown.length} of ${finished.length}; the older ones are in the ticket files` : ''}`,
    shown, (t) => `${row(t)} · ${t.closed_at ? ctFmt(t.closed_at) : t.closed}`
      + `${t.pr ? ` · [PR #${t.pr}](${REPO_URL}/pull/${t.pr})` : ''}`);
  // Idempotent on purpose: only touch the files when the CONTENT changed, so a
  // regenerated-but-identical board stays byte-stable and the published mirror
  // (check_published.mjs compares it verbatim) does not go stale merely because
  // `check` ran after `publish.sh`. The timestamp is excluded from the diff and
  // only rewritten alongside a real change.
  const settle = (file, next) => {
    const cur = existsSync(file) ? readFileSync(file, 'utf8') : '';
    const bare = (x) => x.replace(/generated_ct.*|generated by.*/g, '');
    if (bare(cur) === bare(next)) return false;
    writeFileSync(file, next);
    return true;
  };
  settle(BOARD, md);

  const strip = tickets.map(({ file, body, error, ...rest }) => ({
    ...rest, queue_rank: WORKABLE.includes(rest.state) ? rank(rest) : null,
  }));
  const wrote = settle(JSON_OUT, JSON.stringify({ project: 'chicago-4d',
    generated_ct: at, tickets: strip }, null, 2) + '\n');
  // T-0154: this tool is the WRITER of tickets.json, so it carries the file to
  // the one published path publish.sh copies it to. Only on a real rewrite —
  // see MIRROR's note on why a blanket refresh would weaken check_published.
  // `wrote` OR absent — see MIRROR's note. Untracked means a clone can hold a
  // freshly generated source beside no mirror at all, which is not staleness.
  if (wrote || !existsSync(MIRROR)) mirrorTickets();
}

/**
 * Carry tickets.json to `site/chicago/4d/tickets.json`, the verbatim copy
 * `tools/publish.sh` makes and `tools/check_published.mjs` compares byte for
 * byte. Returns true when it moved bytes, so the caller can say so.
 */
function mirrorTickets() {
  if (!existsSync(path.dirname(MIRROR))) return false;   // never published: leave it that way
  const src = readFileSync(JSON_OUT);
  if (existsSync(MIRROR) && readFileSync(MIRROR).equals(src)) return false;
  writeFileSync(MIRROR, src);
  console.log('   tickets.json mirrored to site/chicago/4d/ (T-0154)');
  return true;
}

/* ----------------------------------------------------------------- check */

function check(tickets) {
  const problems = [];
  const seen = new Map();
  for (const t of tickets) {
    const at = path.basename(t.file);
    if (t.error) { problems.push(`${at}: ${t.error}`); continue; }
    if (!/^T-\d{4}$/.test(t.id ?? '')) problems.push(`${at}: bad id "${t.id}"`);
    if (seen.has(t.id)) {
      problems.push(`${at}: DUPLICATE id ${t.id} (also ${seen.get(t.id)}) — two branches each `
        + 'assigned it. `node tools/ticket.mjs restamp <file>` renumbers the younger one');
    }
    seen.set(t.id, at);
    if (!STATES.includes(t.state)) problems.push(`${at}: state "${t.state}" is not one of ${STATES.join('/')}`);
    if (!EPICS.includes(t.epic)) problems.push(`${at}: epic "${t.epic}" is not one of ${EPICS.join('/')}`);
    if (!BY.includes(t.requested_by)) problems.push(`${at}: requested_by "${t.requested_by}"`);
    if (!t.title) problems.push(`${at}: no title`);
    if (t.state === 'done' && !t.pr) problems.push(`${at}: done without a pr — the closing PR is the receipt`);
    if (t.state === 'done' && !t.closed) problems.push(`${at}: done without a closed date`);
    // The instant, not just the day (since 2026-09-04). `closed` alone cannot
    // order two tickets finished on the same day, which is how the board came to
    // fall back on ticket id. Only tickets closed AFTER this landed are held to
    // it: the 312 finished before it are honest history, not a hole, and a branch
    // cut before the tool changed must still close cleanly on merge day.
    if (t.closed_at && Number.isNaN(Date.parse(t.closed_at))) {
      problems.push(`${at}: closed_at "${t.closed_at}" is not a timestamp Date.parse can read`);
    }
    if (t.state === 'done' && !t.closed_at && String(t.closed ?? '') >= CLOSED_AT_SINCE) {
      problems.push(`${at}: done on ${t.closed} without closed_at — close with `
        + '`node tools/ticket.mjs done ' + `${t.id} --pr N\`, which stamps the instant; a `
        + 'hand-written close loses the finish order');
    }
    if (t.state?.startsWith('blocked') && !t.blocked_on) {
      problems.push(`${at}: ${t.state} without blocked_on — a block with no stated question is an abandonment`);
    }
    // …AND THE OTHER HALF: a `blocked_on` that names a ticket which has FINISHED.
    // T-0465, T-0466 and T-0467 all read `blocked_on: T-0464` on the day after
    // T-0464 closed (#1257), and they are the first three lines of SOUTH THROUGH
    // TIME. Nothing had to read the field for it to do damage: a run picking work
    // off this queue opens the top ticket, sees another ticket's id in
    // `blocked_on`, and steps over it — which is how the band's lead sat unclaimed
    // while the run below it was taken. The blocker's own state is the receipt, so
    // ask it here rather than trusting the field to be swept by hand.
    // SCOPED TO TICKETS STILL IN THE QUEUE, and the scope is the whole point.
    // 16 tickets on dev named a finished blocker and only THREE of them were
    // workable — the three above. The other 13 sit on tickets that are themselves
    // `done` or `withdrawn`, where the field is honest history nobody chooses
    // work from; failing the gate on those would be 13 lines of noise guarding
    // nothing, and the next person would weaken the whole check to shut it up.
    if (WORKABLE.includes(t.state) && t.blocked_on
        && /^T-\d+$/.test(String(t.blocked_on).trim())) {
      const on = tickets.find((x) => x.id === String(t.blocked_on).trim());
      if (on && !WORKABLE.includes(on.state)) {
        problems.push(`${at}: in the queue, blocked_on ${on.id}, which is ${on.state}`
          + `${on.pr ? ` (PR #${on.pr})` : ''} — the dependency is SATISFIED, so clear the `
          + 'field. A stale one reads as a live block to anything choosing work.');
      }
    }
    if (!t.body?.trim()) problems.push(`${at}: empty body — a ticket with no ask or acceptance is a title`);
    if (!Object.keys(EFFORT).includes(t.effort)) {
      problems.push(`${at}: effort "${t.effort}" is not one of ${Object.keys(EFFORT).join('/')} `
        + `(measured in RUNS: ${Object.entries(EFFORT).map(([k, v]) => `${k} = ${v}`).join('; ')})`);
    }
    // An L in the queue is a ticket that CANNOT be finished by whoever takes it,
    // so it would produce a half-done ticket and a self-invented "(1/2)" title.
    // Sizing is the author's job, not the claimant's.
    if (t.effort === 'L' && WORKABLE.includes(t.state)) {
      problems.push(`${at}: effort L is in the queue — ${EFFORT.L}. `
        + `Run \`node tools/ticket.mjs split ${t.id} "first piece" "second piece"\`; `
        + 'the children keep its place in the order.');
    }
    if (t.state === 'split' && WORKABLE.includes(t.state)) {
      problems.push(`${at}: a split parent must not sit in the queue — its children carry the work`);
    }
    if (t.parent && !tickets.some((x) => x.id === t.parent)) {
      problems.push(`${at}: parent ${t.parent} does not exist`);
    }
  }
  // The queue must be EXACTLY the workable set: an open ticket missing from the
  // queue is invisible work, and a queued closed ticket sends an agent to a
  // ghost. Order is not checked — order is the owner's.
  const q = queueIds();
  const wantIds = tickets.filter((t) => WORKABLE.includes(t.state)).map((t) => t.id);
  const ledger = new Map(tickets.filter((t) => t.id).map((t) => [t.id, t]));
  for (const id of q) {
    // NOT IN THE LEDGER AT ALL is its own answer, and it is the one T-0217 asked
    // for: a queue line pointing at an id no ticket file carries is a line the
    // owner ranked that now sends whoever reads it to nothing. The old single
    // message called that "not an open ticket", which reads like a ticket that
    // closed — a repair (delete the line) rather than a corruption (find out
    // what was lost).
    if (!ledger.has(id)) {
      problems.push(`QUEUE.md lists ${id}, which is not in the ledger — no ticket file carries `
        + 'that id. A queue line pointing at nothing is a lost ranking, not a stale one: find '
        + 'what the line used to name before deleting it');
    } else if (!wantIds.includes(id)) {
      problems.push(`QUEUE.md lists ${id}, which is not an open ticket (state ${ledger.get(id).state})`);
    }
  }
  for (const id of wantIds) {
    if (!q.includes(id)) problems.push(`open ticket ${id} is missing from QUEUE.md — append it, do not reorder`);
  }
  const dupQ = q.filter((id, i) => q.indexOf(id) !== i);
  for (const id of new Set(dupQ)) problems.push(`QUEUE.md lists ${id} twice`);

  // T-1518. A BLOCKED TICKET IS VISIBLE OR IT IS LOST, and for a month thirteen of
  // them were lost. `blocked-owner` and `blocked-tech` are deliberately outside
  // WORKABLE — they must not be offered as work — and the consequence was never
  // decided: QUEUE.md carries the workable states, so a block dropped the ticket out
  // of the file altogether. Measured on dev 2026-09-21: NINETEEN live tickets in no
  // band at all, thirteen of them waiting on an owner ruling, the oldest opened
  // 2026-08-21. The one class that most needs the owner's eyes was the one class the
  // owner could not see.
  //
  // Band 8b carries them as COMMENTED lines, the way band 8's HOLD list does, so they
  // are visible to a reader and still invisible to the parser. This asks both
  // directions, because either alone rots: a blocked ticket missing from the band is
  // the fault itself returning, and a band line for a ticket that has since unblocked
  // is the band describing a queue that no longer exists.
  // THE TEST IS "NAMED ANYWHERE IN THE FILE", not "carries my prefix". Band 8's HOLD
  // list already holds seven blocked-tech tickets and has since long before this, and
  // a first cut that demanded `# BLOCKED-TECH` reported every one of them as invisible
  // while they sat two screens up in plain sight. A gate that would force a migration
  // to satisfy itself is measuring its own convention rather than the thing it is for.
  const queueSrc = readFileSync(QUEUE, 'utf8');
  const named = new Set([...queueSrc.matchAll(/\bT-\d{3,5}\b/g)].map((m) => m[0]));
  for (const t of tickets) {
    if (!t.state?.startsWith('blocked')) continue;
    if (!named.has(t.id)) {
      problems.push(`${t.id} is ${t.state} and is named nowhere in QUEUE.md — add it to `
        + '`--- 8b. BLOCKED AND WAITING` as a commented `# BLOCKED-OWNER`/`# BLOCKED-TECH` '
        + 'line (or to band 8s HOLD list where it belongs there). A block nobody can see '
        + 'is an abandonment with a state on it.');
    }
  }
  // …AND THE OTHER DIRECTION, scoped to band 8b's own lines, because those are the ones
  // this file writes and is therefore answerable for. A line saying a ticket waits on
  // the owner, for a ticket that has since unblocked, is worse than no line: it is read
  // as current.
  for (const m of queueSrc.matchAll(/^#\s*BLOCKED-(?:OWNER|TECH)\s+(T-\d+)/gm)) {
    const t = ledger.get(m[1]);
    if (!t) {
      problems.push(`QUEUE.md band 8b lists ${m[1]}, which no ticket file carries`);
    } else if (!t.state?.startsWith('blocked')) {
      problems.push(`QUEUE.md band 8b lists ${m[1]} as blocked, but it is ${t.state} — `
        + 'take the line out; a band that describes a queue which has moved on is read '
        + 'as current.');
    }
  }

  // THE LABEL HAS TO NAME THE TICKET (T-0217). Every gate above reads the id and
  // nothing else, so a line carrying one ticket's id and another's title passes
  // all of them: both ids are real, both are open, neither is duplicated. That is
  // exactly the residue `restamp`'s wrong-line bug left on 2026-08-27, and it is
  // what an agent reading QUEUE.md top-down goes and builds. The label is
  // regenerated from `title:`, so the ticket wins and the line is repairable by
  // hand in one edit — the message says which line and what it should read.
  queueLines().forEach((l, n) => {
    const id = queueId(l);
    const t = id && ledger.get(id);
    if (!t || !t.title) return;
    const label = queueLabel(l);
    if (label !== t.title) {
      problems.push(`QUEUE.md line ${n + 1} labels ${id} "${label || '(nothing)'}", but that `
        + `ticket is titled "${t.title}" — the ticket wins; rewrite the line as `
        + `\`${id} — ${t.title}\``);
    }
  });

  // MATERIALISE THE PAIR — this is no longer a staleness complaint (T-0937).
  //
  // It used to be one, on the reasoning that a stale board is the stale-build.json
  // fault wearing a new file name. That reasoning only held while the pair was
  // COMMITTED: the thing that could be stale was the copy in the tree, and the
  // remedy was to run `board` and commit it. Both files are untracked now, so there
  // is no second copy to disagree with the tickets — regenerating IS the answer, and
  // reporting it as a problem would fail the gate on a fresh clone that had simply
  // never built them.
  //
  // The write stays inside `check` deliberately, rather than moving to a caller: the
  // gate is the one thing guaranteed to run on every branch and in CI, so putting the
  // materialisation here is what makes the board exist wherever anything reads it.
  generateBoard(tickets);

  // THE MIRROR PIN (T-0154). `mirrorTickets` above hard-codes where publish.sh
  // puts this file, which is a second copy of one fact — the failure mode this
  // whole tool's design rules are written against. So the fact is pinned: if the
  // copy in publish.sh moves or goes away, this says so rather than letting the
  // two drift into silently mirroring different paths.
  if (existsSync(PUBLISH_SH) && !readFileSync(PUBLISH_SH, 'utf8').includes(PUBLISH_PIN)) {
    problems.push(`tools/publish.sh no longer contains \`${PUBLISH_PIN}\`, which is the copy `
      + 'this tool mirrors on its behalf (T-0154). Reconcile them: change MIRROR in '
      + 'tools/ticket.mjs to publish.sh\'s new destination, or drop the mirroring if '
      + 'publish.sh has stopped carrying tickets.json at all.');
  }
  return problems;
}

/* ------------------------------------------------------------------ main */

const [cmd, ...args] = process.argv.slice(2);
const flag = (name) => { const i = args.indexOf(`--${name}`); return i < 0 ? null : (args[i + 1] ?? true); };
const has = (name) => args.includes(`--${name}`);
const tickets = loadAll();

// CLOSING THE LAST CHILD OF A SPLIT KILLS THE PARENT, AND NOTHING SAID SO.
//
// A split parent counts as live work only while a child is still open (`split_live`);
// close the last one and the parent is spent, and every research unit that defers to
// it by id is stranded exactly as it would be behind a done ticket (T-1237). The
// ledger refuses those units, so the re-derivation fails — but it fails on the
// MERGE, in a tool the closing PR never runs, long after the author has stopped
// looking. The author cannot see it on their own branch either: there the parent
// still has an open child, which is the one they are closing.
//
// Three times on 2026-09-18: #1452 closed T-1313 and stranded nine units on T-1170;
// #1454 closed T-1311 and stranded seven on T-1180. Each cost a full re-derive to
// discover and a merge round to repair.
//
// This does not refuse the close — the close is usually right, and what the stranded
// units need is a new owner, which is a judgement. It says so at the moment the
// author can still act on it, and names what to look for.
function warnIfThisClosedASplit(closed, all) {
  const parentId = closed.parent;
  if (!parentId) return;
  const parent = all.find((t) => t.id === parentId);
  if (!parent || parent.state !== 'split') return;
  const siblings = all.filter((t) => t.parent === parentId);
  const live = siblings.filter((t) => WORKABLE.includes(t.state));
  if (live.length) return;
  console.log('');
  console.log(`  NOTE: ${closed.id} was the last open child of ${parentId}, which is `
    + `\`split\`. A split parent whose children have all closed is SPENT WORK, and any`);
  console.log('  research unit that defers to it by id is now stranded (T-1237). That fails');
  console.log('  the re-derivation, in a tool this PR does not run — so check it here:');
  console.log('');
  console.log(`      grep -rn '"${parentId}"' chicago/4d/tools/*.py chicago/4d/data/research/spend_rulings.json`);
  console.log('');
  console.log('  Anything that hands units to it needs a LIVE owner before this merges.');
}

switch (cmd) {
  /**
   * THE BUDGET (T-1295). Filing is free and working is not, so an unbudgeted `new` is the
   * one lever every run can pull and none of them feels the cost of. Owner, 2026-09-17:
   * "we spent all night and all day working on the research spend and we still have the
   * same number of tickets we started with … I don't want too many tickets and not making
   * any progress."
   *
   * TWO CEILINGS, BOTH REFUSABLE IN WRITING. A branch may add at most NEW_PER_BRANCH
   * tickets, and nothing may be filed once the queue is at QUEUE_CEILING lines. Either
   * refusal is overridden by `--anyway --why "<reason>"`, and the reason is WRITTEN INTO
   * THE TICKET under its own heading — the same trade as `Changelog: none — <why>` and the
   * liberty ledger: a person had to decide and had to sign it.
   *
   * IT IS NOT A BAN ON FILING, it is a prompt to do the cheaper thing first, which the
   * queue's own header already asks for: "Add findings to an existing ticket first." A
   * finding appended to the ticket it was found in costs nothing to read and nothing to
   * schedule; the same finding as a new line costs a claim, a branch, a gate and a merge.
   *
   * SPLIT IS DELIBERATELY EXEMPT. Splitting is how an oversized ticket becomes workable,
   * the gate already REFUSES an effort-L ticket in the queue, and a split replaces its
   * parent rather than adding to the pile.
   */
  case 'new': {
    // Every flag's VALUE has to come out of the title too, or the reason a run gives for
    // filing over the budget ends up IN the ticket's name — caught by case 18 the day the
    // budget shipped, which produced `T-4141-filed-over-the-budget-it-blocks-a-merge-...`.
    const title = args.filter((a) => !a.startsWith('--')
      && a !== flag('epic') && a !== flag('by') && a !== flag('effort') && a !== flag('legacy')
      && a !== flag('after') && a !== flag('why') && a !== flag('base')).join(' ');
    if (!title) { console.error('usage: ticket.mjs new "title" [--after T-NNNN] [--epic E] [--by owner|loop|steward] [--seen] [--needs-bake] [--effort M] [--legacy OLD-ID] [--anyway --why "<reason>"]\n'
      + '  --after T-NNNN  place the new line directly under that ticket, inside its band (a run\'s\n'
      + '                  filings go here — beside the work they serve, never at the foot)'); process.exit(1); }
    // The budget, measured against the base rather than guessed: the tickets THIS BRANCH
    // adds are the ones it is accountable for.
    const QUEUE_CEILING = 140;
    const NEW_PER_BRANCH = 3;
    const anyway = has('anyway');
    const why = flag('why');
    if (anyway && !String(why ?? '').trim()) {
      console.error('`--anyway` was written with no `--why "<reason>"` after it.');
      console.error('The reason is the whole point — say why this must be a ticket rather');
      console.error('than a paragraph on the ticket it was found in. It is written into the file.');
      process.exit(1);
    }
    let addedHere = 0;
    try {
      const base = flag('base') ?? 'origin/dev';
      addedHere = git(['diff', '--diff-filter=A', '--name-only', `${base}...HEAD`, '--', 'chicago/4d/tickets/'])
        .split('\n').filter((l) => /T-\d+-.*\.md$/.test(l.trim())).length;
    } catch { addedHere = 0; }   // no base to compare against is not an accusation
    const queueNow = queueLines().filter((l) => queueId(l)).length;
    const refusal = queueNow >= QUEUE_CEILING
      ? `the queue stands at ${queueNow} lines, at or over its ceiling of ${QUEUE_CEILING}`
      : addedHere >= NEW_PER_BRANCH
        ? `this branch already adds ${addedHere} ticket(s), its limit of ${NEW_PER_BRANCH}`
        : null;
    if (refusal && !anyway) {
      console.error(`ticket.mjs new: REFUSED — ${refusal}.\n`);
      console.error('The queue\'s own header asks for the cheaper thing first: "Add findings to an');
      console.error('existing ticket first." A paragraph on the ticket a finding was found in costs');
      console.error('nothing to read and nothing to schedule. A new line costs a claim, a branch, a');
      console.error('gate and a merge — and the pile is what stops the work being done.\n');
      console.error('If it genuinely has to be its own ticket, say why and it is taken on your word:\n');
      console.error('  node tools/ticket.mjs new "title" --after T-NNNN --anyway --why "<reason>"\n');
      console.error('The reason is written into the ticket. Folding something else out of the queue');
      console.error('also clears the ceiling, and `prune` drops any line whose work has finished.');
      process.exit(1);
    }
    const [id] = mintIds(tickets);
    const t = {
      file: path.join(DIR, `${id}-${slugOf(title)}.md`),
      id, title, state: 'open',
      epic: (flag('epic') ?? 'META').toUpperCase(),
      requested_by: flag('by') ?? 'steward',
      seen: has('seen'), effort: flag('effort') ?? 'M',
      legacy_id: flag('legacy') ?? null,
      opened: today(), closed: null, closed_at: null, pr: null,
      claimed_by: null, claimed_run: null, blocked_on: null,
      needs_bake: has('needs-bake'),
      body: `\n${title}.\n${refusal && anyway
        ? `\n## FILED OVER THE BUDGET, AND HERE IS THE REASON\n\nThe ticket budget refused this: ${refusal}. It was filed anyway, on this reason:\n\n> ${String(why).trim()}\n`
        : ''}\n**Acceptance:** (state it before working — the definition of done, never weakened to pass)\n`,
    };
    writeTicket(t);
    // Where the line goes. `--after` is the run's placement; a bare `new` is the owner's
    // own filing, or a run that found nothing to stand beside — and the message says
    // which happened, so a fallback is never mistaken for a choice.
    const afterRaw = flag('after');
    const after = afterRaw ? (/^\d+$/.test(afterRaw) ? idOf(+afterRaw) : afterRaw.toUpperCase()) : null;
    let where;
    if (after && queueInsertAfter(t, after)) {
      where = `placed directly under ${after}, inside its band`;
    } else {
      queueAppend(t);
      where = after
        ? `${after} is not in QUEUE (closed, blocked, or mistyped) — appended to the bottom instead; move it or pick a live anchor`
        : 'appended to QUEUE bottom — the owner orders it; a run should pass --after T-NNNN';
    }
    generateBoard(loadAll());
    console.log(`${id} created → ${path.relative(ROOT, t.file)} (${where})`);
    break;
  }
  case 'claim': {
    const t = find(tickets, args[0]);
    if (!WORKABLE.includes(t.state)) { console.error(`${t.id} is ${t.state}, not claimable`); process.exit(1); }
    // An L ticket cannot be finished in the run that claims it, so claiming one
    // guarantees a half-done ticket and a PR that invents its own "(1/2)".
    if (t.effort === 'L') {
      console.error(`${t.id} is effort L — ${EFFORT.L}.\n`
        + `Split it first, and the pieces keep this ticket's place in the queue:\n`
        + `  node tools/ticket.mjs split ${t.id} "first piece" "second piece"`);
      process.exit(1);
    }
    // A claim only reaches `dev` when its PR merges, so a run that opens a PR and
    // does not merge it leaves the ticket reading `open` to the NEXT run, which
    // then does the same work twice. That happened to T-0062 on 2026-08-19: run
    // 943 opened PR #258 green and deferred the merge on a smoke it could not
    // finish; run 944 read the queue, saw T-0062 open at the top, and rebuilt it
    // from scratch on its own branch. Two runs, one ticket, one of them binned.
    //
    // The remote branch list is the one piece of shared state a run CAN see
    // before it starts, so look there. Best-effort by construction: no network,
    // no git, or a detached checkout just means no warning — never a false stop.
    const rival = remoteBranchesFor(t.id, t.state);
    if (rival.length && !has('force')) {
      console.error(`${t.id} looks like it is already being worked:\n`
        + rival.map((b) => `  ${b}`).join('\n')
        + `\nCheck whether that branch has an open PR before starting. If it is stale,\n`
        + `or that branch is yours, claim it anyway:\n`
        + `  node tools/ticket.mjs claim ${t.id} --force`);
      process.exit(1);
    }
    const claimedBy = `${flag('by') ?? 'run'} ${new Date().toLocaleString('en-US', { timeZone: 'America/Chicago' })} CT`;
    // WHICH run holds it. `claimed_by` says when; when five slices run at once
    // that is not enough to tell whose ticket this is, or to open the log of the
    // run that went quiet with it. `--run <url>` overrides for a hand claim.
    const claimedRun = flag('run') ?? runUrl();

    // THE LOCK, taken before a line of work — see takeClaimLock above for why the
    // branch scan alone could never have caught the six duplicates of 2026-09-11.
    // `--no-lock` is for a checkout with no remote at all; it is not a way past a
    // live claim, which is what `--force` is for.
    if (!has('no-lock')) {
      const lock = takeClaimLock(t.id, claimedBy, claimedRun, { steal: has('force') });
      if (lock.unknown) {
        console.error(`  note: claim lock not taken (${lock.unknown}) — proceeding, as the branch scan does`);
      } else if (!lock.held) {
        console.error(`${t.id} IS ALREADY CLAIMED on the remote — another run holds it.\n`
          + `  ${claimBranch(t.id)}  ${lock.by ? `— ${lock.by.split('\n')[0]}` : ''}\n`
          + `  ${sinceWords(lock.ageHours)}${lock.raced ? ', and another run took it while this one looked' : ''}\n`
          + (lock.by?.includes('run: ') ? `  ${lock.by.split('\n').find((l) => l.startsWith('run: '))}\n` : '')
          + `\nThat run's claim will not reach \`dev\` until its PR merges, which is exactly\n`
          + `why this check does not read \`dev\`. Take the next workable ticket instead:\n`
          + `  node tools/ticket.mjs list --workable\n`
          + `A claim older than ${RUN_HOURS}h is a dead run and is stolen automatically. To override now:\n`
          + `  node tools/ticket.mjs claim ${t.id} --force`);
        process.exit(1);
      } else if (lock.stolen) {
        console.log(`  stole a dead claim (${sinceWords(lock.stolen.ageHours)}) — ${lock.stolen.by?.split('\n')[0] ?? 'holder unknown'}`);
      }
    }

    t.state = 'claimed';
    t.claimed_by = claimedBy;
    t.claimed_run = claimedRun;
    writeTicket(t); generateBoard(loadAll());
    console.log(`${t.id} claimed`);
    break;
  }
  case 'done': {
    const t = find(tickets, args[0]);
    t.state = 'done'; t.closed = today(); t.closed_at = nowIso(); t.pr = flag('pr');
    if (!t.pr) { console.error('done needs --pr N — the closing PR is the receipt'); process.exit(1); }
    writeTicket(t); queueRemove(t.id); generateBoard(loadAll());
    // THE CLAIM IS KEPT, AND COLLECTED BY AGE (T-1351). This used to give the marker
    // back here. The reasoning left behind by T-1145 — which moved `split` off the
    // handback for the same fault — said why `done` was left alone: "`done` and
    // `withdraw` end a run: rule 7 has its PR merging minutes later, so the window
    // where `dev` disagrees is short."
    //
    // THE WINDOW IS NOT SHORT WHEN THE PR CANNOT MERGE, and on 2026-09-18 that cost
    // two runs on T-1333:
    //
    //   21:02:57  run 35389718070 claims T-1333, works it, runs `done --pr 1477`,
    //             and the release here deletes claim/t-1333 while #1477 is unmerged
    //   22:10     #1477 opens and cannot gate — it is `dirty`, and GitHub builds no
    //             merge commit for a conflicted PR, so no check ever runs
    //   22:45:27  run 35402702816 reads `dev`, where T-1333 is still `open` because
    //             #1477 has not landed, finds no lock, and claims the same ticket
    //   23:15     #1480 opens: a second, independent implementation of one acceptance
    //
    // Both claims were legitimate — 1h42m apart, well inside RUN_HOURS — and both runs
    // were correct by every rule as written. A run cannot know when its PR merges, so
    // any handback here is a bet on that interval, and it is lost exactly when the
    // queue is congested and a duplicate is most expensive.
    //
    // So the marker outlives the run and `claims --sweep` collects it by age, which is
    // what RUN_HOURS is for and where `split` has stood since T-1145. The cost is
    // stated rather than hidden: an abandoned PR holds its ticket for up to three
    // hours instead of being re-offered at once.
    console.log(`${t.id} done (PR #${t.pr}) — removed from QUEUE`);
    warnIfThisClosedASplit(t, loadAll());
    break;
  }
  case 'block': {
    const t = find(tickets, args[0]);
    t.state = has('owner') ? 'blocked-owner' : 'blocked-tech';
    t.blocked_on = flag('on');
    if (!t.blocked_on) { console.error('block needs --on "the question or the missing thing"'); process.exit(1); }
    writeTicket(t); queueRemove(t.id); generateBoard(loadAll());
    // THE CLAIM IS KEPT, AND COLLECTED BY AGE (T-1351). This used to give the marker
    // back here. The reasoning left behind by T-1145 — which moved `split` off the
    // handback for the same fault — said why `done` was left alone: "`done` and
    // `withdraw` end a run: rule 7 has its PR merging minutes later, so the window
    // where `dev` disagrees is short."
    //
    // THE WINDOW IS NOT SHORT WHEN THE PR CANNOT MERGE, and on 2026-09-18 that cost
    // two runs on T-1333:
    //
    //   21:02:57  run 35389718070 claims T-1333, works it, runs `done --pr 1477`,
    //             and the release here deletes claim/t-1333 while #1477 is unmerged
    //   22:10     #1477 opens and cannot gate — it is `dirty`, and GitHub builds no
    //             merge commit for a conflicted PR, so no check ever runs
    //   22:45:27  run 35402702816 reads `dev`, where T-1333 is still `open` because
    //             #1477 has not landed, finds no lock, and claims the same ticket
    //   23:15     #1480 opens: a second, independent implementation of one acceptance
    //
    // Both claims were legitimate — 1h42m apart, well inside RUN_HOURS — and both runs
    // were correct by every rule as written. A run cannot know when its PR merges, so
    // any handback here is a bet on that interval, and it is lost exactly when the
    // queue is congested and a duplicate is most expensive.
    //
    // So the marker outlives the run and `claims --sweep` collects it by age, which is
    // what RUN_HOURS is for and where `split` has stood since T-1145. The cost is
    // stated rather than hidden: an abandoned PR holds its ticket for up to three
    // hours instead of being re-offered at once.
    console.log(`${t.id} → ${t.state}`);
    break;
  }
  case 'unblock': {
    const t = find(tickets, args[0]);
    t.state = 'open'; t.blocked_on = null;
    writeTicket(t); queueAppend(t); generateBoard(loadAll());
    console.log(`${t.id} → open (appended to QUEUE bottom; the owner may move it up)`);
    break;
  }
  case 'withdraw': {
    const t = find(tickets, args[0]);
    t.state = 'withdrawn'; t.closed = today(); t.closed_at = nowIso(); t.blocked_on = flag('why') ?? t.blocked_on;
    writeTicket(t); queueRemove(t.id); generateBoard(loadAll());
    // THE CLAIM IS KEPT, AND COLLECTED BY AGE (T-1351). This used to give the marker
    // back here. The reasoning left behind by T-1145 — which moved `split` off the
    // handback for the same fault — said why `done` was left alone: "`done` and
    // `withdraw` end a run: rule 7 has its PR merging minutes later, so the window
    // where `dev` disagrees is short."
    //
    // THE WINDOW IS NOT SHORT WHEN THE PR CANNOT MERGE, and on 2026-09-18 that cost
    // two runs on T-1333:
    //
    //   21:02:57  run 35389718070 claims T-1333, works it, runs `done --pr 1477`,
    //             and the release here deletes claim/t-1333 while #1477 is unmerged
    //   22:10     #1477 opens and cannot gate — it is `dirty`, and GitHub builds no
    //             merge commit for a conflicted PR, so no check ever runs
    //   22:45:27  run 35402702816 reads `dev`, where T-1333 is still `open` because
    //             #1477 has not landed, finds no lock, and claims the same ticket
    //   23:15     #1480 opens: a second, independent implementation of one acceptance
    //
    // Both claims were legitimate — 1h42m apart, well inside RUN_HOURS — and both runs
    // were correct by every rule as written. A run cannot know when its PR merges, so
    // any handback here is a bet on that interval, and it is lost exactly when the
    // queue is congested and a duplicate is most expensive.
    //
    // So the marker outlives the run and `claims --sweep` collects it by age, which is
    // what RUN_HOURS is for and where `split` has stood since T-1145. The cost is
    // stated rather than hidden: an abandoned PR holds its ticket for up to three
    // hours instead of being re-offered at once.
    console.log(`${t.id} withdrawn`);
    break;
  }
  case 'restamp': {
    // The duplicate-id remedy. Renumber ONE ticket (the younger of a colliding
    // pair) to the next free id, renaming its file with it.
    //
    // Takes a path as readily as a bare filename or an id: with two files sharing
    // an id, `find` by id cannot tell them apart, so the FILE is the only way to
    // say which one moves — and the first thing anyone reaches for is the path
    // `check` just printed.
    const arg = args[0] ?? '';
    const t = tickets.find((x) => x.file === path.resolve(arg))
      ?? tickets.find((x) => path.basename(x.file) === path.basename(arg))
      ?? find(tickets, arg);
    const old = t.id;
    // KEEP ITS PLACE IN THE QUEUE. This used to remove the old line and append
    // the new one at the BOTTOM, so renumbering a ticket silently re-prioritised
    // it — and the owner orders that file. A restamp changes a ticket's NUMBER
    // and nothing else about it.
    //
    // AND KEEP THE OTHER TICKET'S. The comment above says the FILE is the only
    // way to name which of a colliding pair moves; the queue edit then went back
    // to matching on the shared id, so it rewrote whichever of the two lines the
    // owner had ranked higher (T-0217). `queueIndexOf` resolves the line by id
    // AND label, so the line that moves is the one written from THIS file.
    const { i: line, byLabel } = queueIndexOf(old, t.title);
    [t.id] = mintIds(tickets);
    const dest = path.join(DIR, `${t.id}-${slugOf(t.title)}.md`);
    writeTicket(t); renameSync(t.file, dest); t.file = dest;
    if (line >= 0) queueReplaceAt(line, [`${t.id} — ${t.title}`]);
    else if (WORKABLE.includes(t.state)) queueAppend(t);
    // Say so when the label could not name the line. With a duplicate id in the
    // queue that means the wrong line may just have moved — the exact fault this
    // repair is for — and the reader is the only one who can tell.
    if (line >= 0 && !byLabel && queueIds().filter((x) => x === old).length) {
      console.log(`   NOTE: no queue line carried this ticket's title, so line ${line + 1} `
        + `was picked by id alone and another ${old} line remains. Check QUEUE.md.`);
    }
    generateBoard(loadAll());
    console.log(`${old} → ${t.id}${line >= 0 ? ' (queue place kept)' : ''}`);
    break;
  }
  case 'split': {
    // The remedy for an L ticket, and for any ticket a run discovers is bigger
    // than one demonstration. The parent becomes the grouping record (state
    // `split`, out of the queue) and the children take its place in the order.
    const t = find(tickets, args[0]);
    const titles = args.slice(1).filter((a) => !a.startsWith('--'));
    if (titles.length < 2) {
      console.error(`usage: ticket.mjs split ${t.id} "first piece" "second piece" [...]`);
      process.exit(1);
    }

    // A SPLIT IS NOT REPEATABLE (T-1481, 2026-09-21). There was no guard on the
    // parent's own state, so a ticket that already carried children could be split
    // a SECOND time — and on 2026-09-20 T-1452 was, four hours apart:
    //
    //   13:48  run 35529393603 claims T-1452 and splits it into T-1480/T-1481/T-1482
    //   17:52  run 35542539851 reads T-1452, finds it splittable, and splits it AGAIN
    //          into T-1494/T-1495/T-1496 — the same twenty-six roofs, renumbered
    //
    // Six tickets and six queue rows for one parcel of work, in pairs that read as
    // unrelated rows: T-1481/T-1494 (the South parcel's eleven roofs), T-1495 against
    // T-1480's live child T-1484 (the North parcel's nine), T-1482/T-1496 (the three
    // platted blocks' six). T-1494 migrated the South eleven and merged as #1600; its
    // twin T-1481 was still `open` at the head of `list --workable` the next morning,
    // and two slices were working T-1482 while T-1496 waited below it for a third.
    //
    // THE CLAIM LOCK CANNOT CATCH THIS. Both runs claimed legitimately, hours apart,
    // and the duplicate is minted by the split itself — the lock guards the parent
    // for one run's lifetime, not for the life of the children it leaves behind.
    // The children ARE the ticket once the split lands, so a parent that is still
    // too big is split one level DOWN: that is what T-1480 -> T-1483/T-1484 did.
    if (t.state === 'split') {
      const kids = tickets.filter((k) => k.parent === t.id);
      console.error(`${t.id} is already split — splitting it again mints a duplicate of every piece.`);
      console.error(`Its children carry the work${kids.length ? ':' : '.'}`);
      for (const k of kids) console.error(`  ${k.id}  ${String(k.state).padEnd(10)} ${k.title}`);
      console.error(`Split one of THOSE if a piece is still more than one run's demonstration.`);
      process.exit(1);
    }
    if (['done', 'withdrawn'].includes(t.state)) {
      console.error(`${t.id} is ${t.state} — a finished ticket has no work left to split.`);
      console.error(`File what remains with \`ticket.mjs new\` instead.`);
      process.exit(1);
    }
    const minted = mintIds(tickets, titles.length);
    const rows = [];
    titles.forEach((title, n) => {
      const id = minted[n];
      const child = {
        file: path.join(DIR, `${id}-${slugOf(title)}.md`),
        id, title, state: 'open', epic: t.epic, requested_by: t.requested_by,
        seen: t.seen, effort: 'S', legacy_id: t.legacy_id, parent: t.id,
        opened: today(), closed: null, closed_at: null, pr: null,
        claimed_by: null, claimed_run: null, blocked_on: null,
        needs_bake: false,
        body: `\n${title}.\n\nPiece ${n + 1} of ${titles.length} of **${t.id} — ${t.title}**, `
          + `split because the parent needed more than one run's demonstration to be done. `
          + `The parent keeps the full ask and its links; this ticket owns one slice of it.\n\n`
          + `**Acceptance:** (state it before working — one demonstration, never weakened to pass)\n`,
      };
      writeTicket(child);
      rows.push(`${id} — ${title}`);
      console.log(`  ${id}  ${title}`);
    });
    queueReplace(t.id, rows, t.title);
    t.state = 'split'; t.closed = today(); t.closed_at = nowIso();
    writeTicket(t); generateBoard(loadAll());
    // SPLIT KEEPS THE CLAIM. It used to give it back, "exactly as `done`, `block`
    // and `withdraw` do", because on 2026-09-14 thirteen of the nineteen markers
    // standing on the remote belonged to tickets in state `split`. That reasoning
    // was right about the litter and wrong about the lock, and T-1145 is what it
    // cost on 2026-09-17:
    //
    //   03:38:16  run 35200021551 claims T-1145, splits it, and the release here
    //             deletes claim/t-1145 while its own PR is still unopened.
    //   03:57:43  run 35202200830 reads `dev`, where the split has not landed and
    //             T-1145 is still `open` at the top of the queue, finds no lock,
    //             and claims the same ticket.
    //
    // Both runs then split T-1145 into DIFFERENT children — #1386 minted T-1224/
    // T-1225/T-1226, #1387 minted T-1223/T-1224/T-1229 — and built plural dated
    // roles twice, two ways, with colliding ids. Nineteen minutes apart, and the
    // lock that exists to stop exactly this had been handed back by the first run.
    //
    // A SPLIT IS NOT FINISHED WORK. `done` and `withdraw` end a run: rule 7 has
    // its PR merging minutes later, so the window where `dev` disagrees is short.
    // A split is the OPPOSITE — the run carries on for another hour working a
    // child, and for that whole hour `dev` still offers the parent. That is the
    // widest window any terminal state has, and it is the one that was opened.
    //
    // The litter is collected by age instead, which is what `RUN_HOURS` is for:
    // `ticket.mjs claims --sweep` deletes any marker older than three hours and
    // `.github/steward/pr-lap.sh` runs it on every lap. So a marker outlives the
    // run that took it by at most a sweep, and never outlives the merge that
    // makes the split visible.
    //
    // `tools/test_ticket_claim_split.mjs` holds both halves: the lock stands after
    // a split, and a second claim on the split parent is refused while it does.
    console.log(`${t.id} → split into ${titles.length}; children hold its place in QUEUE`);
    break;
  }
  case 'list': {
    const want = flag('state');
    const shown = tickets.filter((t) => has('workable') ? WORKABLE.includes(t.state) : (!want || t.state === want));
    const order = queueIds();
    shown.sort((a, b) => (order.indexOf(a.id) + 1 || 9999) - (order.indexOf(b.id) + 1 || 9999));
    for (const t of shown) {
      console.log(`${t.id}  ${String(t.state).padEnd(13)} ${t.requested_by === 'owner' ? 'OWNER ' : '      '}${t.title}`);
    }
    break;
  }
  /**
   * PRUNE — drop every queue line whose ticket is no longer workable on THIS tree.
   *
   * WHY (2026-09-17). Three branches went red on the same day on `ticket.mjs check`
   * — #1387, #1389, #1392 — each of them listing a ticket that had finished on `dev`
   * while the branch was open. It is the commonest red the lap leaves behind, and it
   * is entirely mechanical: a branch's QUEUE.md is a snapshot, `dev` closes tickets
   * under it, and the two disagree until somebody deletes a line by hand.
   *
   * It is not untidiness. A done ticket at the top of the queue is the exact shape of
   * available work, and it is how T-0429 came to be rebuilt across 116 files.
   *
   * THE RULE IS THE GATE'S OWN, not a second opinion: `check` refuses a queue line
   * whose ticket is not open/claimed/review, so that is what this removes. It can
   * only DELETE a line, never add or reorder one, which is what makes it safe for an
   * automaton to run — the owner's ranking is untouched and a line that should stay
   * cannot be moved by it. `--dry-run` prints without writing.
   */
  case 'prune': {
    const workable = new Set(tickets.filter((t) => WORKABLE.includes(t.state)).map((t) => t.id));
    const state = new Map(tickets.map((t) => [t.id, t.state]));
    const lines = queueLines();
    const dropped = [];
    const kept = lines.filter((l) => {
      const id = queueId(l);
      if (!id || workable.has(id)) return true;
      dropped.push(`${id} (${state.get(id) ?? 'no such ticket'})`);
      return false;
    });
    if (!dropped.length) { console.log('queue prune: nothing to drop — every line is workable'); break; }
    if (has('dry-run')) {
      console.log(`queue prune: ${dropped.length} line(s) WOULD be dropped — ${dropped.join(', ')}`);
      break;
    }
    writeFileSync(QUEUE, kept.join('\n').replace(/\n+$/, '\n'));
    generateBoard(loadAll());
    console.log(`queue prune: dropped ${dropped.length} line(s) — ${dropped.join(', ')}`);
    break;
  }
  /**
   * THE OTHER HALF OF `prune`, AND THE ONE THE LAP COULD NOT DO (T-1285).
   *
   * `prune` DELETES a queue line whose ticket is finished. The fault that actually
   * held the pull-request queue shut runs the other way: a line the BASE added while
   * a branch was open, LOST by the merge. QUEUE.md is in pr-lap.sh's `GENERATED` set,
   * so a conflict there is cleared by taking a side and letting a tool rewrite the
   * file — and for this file the tool is `board`, which regenerates BOARD.md from the
   * queue and can only ever preserve what the side it took already said. Take the
   * branch's side and every line `dev` added is gone.
   *
   * It is not hypothetical and it is not rare. Measured 2026-09-17 on the two PRs the
   * lap had just pushed: #1400 was missing 28 of dev's queue lines and #1392 was
   * missing 27, both red on the single gate step `ticket queue`, one of 439 — and
   * `prune` ran on both, correctly, and could do nothing. Every line was one of the 27
   * reconstruction tickets dev took in #1402 plus T-1177's retitle.
   *
   * WHAT IT WILL NOT DO IS INVENT AN ORDER. The queue is the OWNER's ordering; that is
   * why `prune` only deletes and why `new` refuses to guess a position without
   * `--after`. So this does not append and it does not sort: it takes the base's queue
   * whole, then walks the branch's queue and puts back each line the base does not
   * carry AFTER THE SAME LINE IT FOLLOWED ON THE BRANCH. A line whose predecessor is
   * not in the base's queue either — the only case with no answer — goes to the foot,
   * which is where `new` puts a line it cannot place, and the report says so.
   *
   *   node tools/ticket.mjs reconcile [--base origin/dev] [--dry-run]
   */
  case 'reconcile': {
    const base = flag('base') ?? 'origin/dev';
    let baseLines;
    try {
      baseLines = git(['show', `${base}:chicago/4d/tickets/QUEUE.md`]).split('\n');
    } catch {
      console.error(`queue reconcile: cannot read ${base}:chicago/4d/tickets/QUEUE.md — `
        + 'fetch the base first, or pass --base <ref>.');
      process.exit(1);
    }
    // IT WORKS ON THE BRANCH'S FILE, NOT THE BASE'S, AND THE FIRST CUT HAD THAT BACKWARDS.
    //
    // Rebuilding on top of `baseLines` restored the ticket lines correctly and threw away
    // every NON-ticket line the branch had written — the band headers, the owner's ordering
    // notes, the preamble. It was caught the day it shipped: the owner's ruling of
    // 2026-09-17 renumbered the parked jaunts bands from 5F-5J to 6 and wrote the
    // fall-through rule into the header, the lap ran, and #1413 merged WITHOUT either,
    // because the lap's own reconcile had quietly taken dev's headers back. A tool that
    // silently reverts the thing a branch came to say is worse than the fault it fixes.
    //
    // So: start from the BRANCH's file, keep its prose exactly, and only ADD the ticket
    // lines the base carries and the branch has lost — each after the line it follows in
    // the BASE, which is the owner's ranking of it. Nothing here deletes a line; `prune`
    // owns deletion and applies the gate's own rule.
    const mine = queueLines();
    const mineIds = new Set(mine.map(queueId).filter(Boolean));
    const out = [...mine];
    const restored = [];
    const skipped = [];
    // …AND A LINE THE BRANCH CLOSED IS NOT A LINE THE BRANCH LOST.
    //
    // The base's queue is the base's view of what is open. A branch that CLOSES a
    // ticket removes its line, and to this reconcile that is indistinguishable from
    // the loss it exists to repair — so it put the line back, and `check` then failed
    // the branch for queueing a ticket the same branch had marked done. Measured on
    // #1454 (T-1311): reconcile restored two lines, one genuinely lost and one the PR
    // had just closed. The branch's own ticket files are the authority on state here,
    // exactly as they are for `check`, so a base line whose ticket is no longer
    // workable is reported and left out rather than restored.
    const workable = new Set(tickets.filter((t) => WORKABLE.includes(t.state)).map((t) => t.id));
    let prev = null;
    for (const line of baseLines) {
      const id = queueId(line);
      if (!id) continue;
      if (!mineIds.has(id) && !workable.has(id)) {
        const t = tickets.find((x) => x.id === id);
        skipped.push(`${id} (${t ? t.state : 'no ticket file'})`);
        prev = id;
        continue;
      }
      if (!mineIds.has(id)) {
        const at = prev === null ? -1 : out.findIndex((l) => queueId(l) === prev);
        if (at >= 0) { out.splice(at + 1, 0, line); restored.push(`${id} (after ${prev})`); }
        else {
          const top = out.findIndex((l) => queueId(l) !== null);
          if (top < 0) { out.push(line); restored.push(`${id} (to the foot — this queue has no lines)`); }
          else { out.splice(top, 0, line); restored.push(`${id} (to the top — it led the base's queue)`); }
        }
      }
      prev = id;
    }
    const lost = restored.length;
    if (skipped.length) {
      console.log(`queue reconcile: ${skipped.length} line(s) of the base were NOT restored — `
        + 'this branch closed them:');
      for (const row of skipped) console.log(`  ${row}`);
    }

    // AND THE LABEL FOLLOWS THE TICKET, because `check` already rules that it does:
    // "the ticket wins; rewrite the line as …". A title edited on the base while a branch
    // was open leaves the branch's line carrying the old words, and the gate refuses it —
    // #1417 went red on exactly that, one step of 441, after T-1276 was retitled on dev.
    // Rewriting a label can never lose the owner's intent the way reordering could: the
    // ORDER is untouched and the title is the ticket's own.
    const relabelled = [];
    const byId = new Map(tickets.map((t) => [t.id, t]));
    for (let i = 0; i < out.length; i += 1) {
      const id = queueId(out[i]);
      const t = id && byId.get(id);
      if (!t || !t.title) continue;
      const label = queueLabel(out[i]);
      if (label && label !== t.title) {
        out[i] = `${id} — ${t.title}`;
        relabelled.push(id);
      }
    }
    if (has('dry-run')) {
      console.log(`queue reconcile: ${lost} line(s) of ${base} WOULD come back, `
        + `${relabelled.length} label(s) WOULD follow their ticket; `
        + "this branch's own lines and its headers are untouched");
      for (const r of restored) console.log(`  ${r}`);
      break;
    }
    writeFileSync(QUEUE, out.join('\n').replace(/\n+$/, '\n'));
    generateBoard(loadAll());
    console.log(`queue reconcile: ${lost} line(s) of ${base} the merge had lost are back, `
      + `${relabelled.length} label(s) rewritten from their ticket`
      + `${relabelled.length ? ` (${relabelled.join(', ')})` : ''}; `
      + "this branch's own lines and its headers are untouched");
    for (const r of restored) console.log(`  ${r}`);
    break;
  }
  case 'board': generateBoard(tickets); console.log(`BOARD.md + tickets.json regenerated (${tickets.length} tickets)`); break;
  /**
   * WHAT IS BEING WORKED ON RIGHT NOW — the one question the files cannot answer.
   *
   * A ticket's state lives in its file, and the file only reaches `dev` when its PR
   * merges, so BOARD.md can show the queue and what has landed but never what is in
   * flight. The remote branch list can: a run pushes its branch in its first commit,
   * hours before anything merges. So read the branches and map them back to tickets.
   *
   * Three things fall out of that mapping, and each is worth seeing:
   *   - a branch on an OPEN ticket — that is the loop, working, right now;
   *   - a branch on a DONE ticket — a leftover, safe to delete;
   *   - a ticket the files call `claimed` with no branch — an abandoned claim.
   *
   * A FOURTH, since T-0852: a branch older than a run whose ticket the files still
   * call `claimed`. That used to be filed under "cold", which said it was finished
   * or litter when it was neither — see `inflightState` for the cohort that cost.
   */
  case 'inflight': {
    const here = currentBranch();
    // `--branches-json <file>` is the offline demonstration, the same device
    // `landed --pr-json` uses and for the same reason: the correct answer against
    // the real remote changes hourly, so the gate runs on a constructed branch list
    // ([{ name, age_hours }]) and asserts the READING rather than the day.
    const fixtureFile = flag('branches-json');
    const branches = typeof fixtureFile === 'string'
      ? JSON.parse(readFileSync(fixtureFile, 'utf8')).map((b) => ({
          name: b.name, age: b.age_hours === null || b.age_hours === undefined ? null : Number(b.age_hours),
        }))
      : remoteBranches().map((b) => ({ name: b.name, age: branchAgeHours(b.sha) }));
    const locked = lockedIds(branches);
    const rows = [];
    for (const b of branches) {
      const t = tickets.find((x) => branchCarries(b.name, x.id));
      if (t) rows.push({ b: b.name, t, age: b.age, how: inflightState(t.state, b.age, locked.has(t.id)) });
    }

    // THE PR LIST, ASKED BEFORE ANYTHING IS PRINTED (T-1155). `recoverable` is the one
    // reading that needs it: a cold branch on an unfinished ticket is either work whose
    // PR merged long ago — litter, T-0429's shape — or work that never got a PR at all
    // and is invisible to every other instrument here. Only this answer tells them apart,
    // so when it does not come, nothing is upgraded and the report says why.
    const prFixtureFile = flag('pr-json');
    // THE FIXTURE MODE REACHES NO NETWORK, EVER. `--branches-json` is the gate's
    // constructed branch list, and its whole value is that the reading it asserts is
    // the tool's and not today's GitHub. If that run were allowed to fall through to
    // the live PR list, `recoverable` would depend on the real repo's merge history
    // and the test would pass or fail by the hour. Supply `--pr-json` to exercise it.
    const offlineFixture = typeof fixtureFile === 'string' && typeof prFixtureFile !== 'string';
    const landed = (has('no-landed') || offlineFixture) ? null : (() => {
      try {
        return collectLanded(tickets, {
          fixture: typeof prFixtureFile === 'string'
            ? JSON.parse(readFileSync(prFixtureFile, 'utf8')) : null,
          maxPages: Math.max(1, Math.min(30, Number(flag('pages')) || 6)),
        });
      } catch { return null; }                       // rule 3: never stop a run
    })();
    // THE OPEN PULL REQUESTS, BY THE BRANCH THEY SIT ON (T-1427). An open PR is the
    // loudest statement there is that a branch's work is visible and somebody's, and
    // until now it was the one thing this report could not see: the fetch asked for
    // closed PRs only, and the projection dropped `head.ref` besides.
    const openPrByRef = new Map();
    for (const pr of (landed?.ok ? landed.pulls : null) ?? []) {
      const ref = pr?.head?.ref;
      if (!ref || pr.merged_at || pr.state !== 'open') continue;
      const prev = openPrByRef.get(ref);
      if (!prev || Number(pr.number) > Number(prev.number)) openPrByRef.set(ref, pr);
    }
    if (landed?.ok) {
      const landedIds = new Set(landed.found.map(({ t }) => t.id));
      // A branch that ever HAD a pull request was never invisible, whatever became of
      // it, so it is not what this reading is for.
      const hadPr = new Set((landed.pulls ?? [])
        .map((pr) => pr?.head?.ref).filter(Boolean));
      for (const r of rows) {
        if (r.how !== 'cold') continue;
        if (!WORKABLE.includes(r.t.state)) continue;
        if (isClaimMarker(r.b)) continue;            // a lock is not work
        // AN OPEN PULL REQUEST OUTRANKS EVERY AGE HEURISTIC HERE. The work is on the
        // remote and readable, so it is not lost; and the cold list's own advice —
        // `git push origin --delete` — would shut somebody's pull request. Neither
        // existing reading is true about it, so it gets its own.
        if (openPrByRef.has(r.b)) { r.how = 'open_pr'; continue; }
        if (landedIds.has(r.t.id) || hadPr.has(r.b)) continue;
        r.how = 'recoverable';
      }
    }

    // Live work first, then the claims that outlived the window, then work nobody can
    // see, then the cold.
    const RANK = { live: 0, held: 1, open_pr: 2, recoverable: 3, cold: 4 };
    rows.sort((a, b) => RANK[a.how] - RANK[b.how] || a.t.id.localeCompare(b.t.id));

    if (!branches.length) {
      console.log('no remote branches readable (no network, or no git) — nothing to report');
      break;
    }
    const live = rows.filter((r) => r.how === 'live');
    const held = rows.filter((r) => r.how === 'held');
    const openPr = rows.filter((r) => r.how === 'open_pr');
    const recoverable = rows.filter((r) => r.how === 'recoverable');
    const cold = rows.filter((r) => r.how === 'cold');
    const age = (r) => ageWords(r.age);
    // Said on every line that has one, not only in the section below: a run reading
    // this list wants the PR number at the branch, not two lists to cross-reference.
    const prNote = (branch) => {
      const pr = openPrByRef.get(branch);
      if (!pr) return '';
      const labels = (pr.labels ?? []).length ? ` · ${pr.labels.join(', ')}` : '';
      return `   · PR #${pr.number} OPEN${labels}`;
    };
    const say = (r) => {
      console.log(`  ${r.t.id}  ${String(r.t.state).padEnd(9)} ${r.t.requested_by === 'owner' ? 'OWNER ' : '      '}${r.t.title}`);
      console.log(`          ↳ ${r.b}${isClaimMarker(r.b) ? '   (claim lock — claimed, nothing pushed yet)' : ''}${r.b === here ? '   ← you are here' : ''}   ${age(r)}${prNote(r.b)}\n`);
    };

    if (has('json')) {
      console.log(JSON.stringify(rows.map((r) => ({
        id: r.t.id, state: r.t.state, branch: r.b, age_hours: r.age, reading: r.how,
        open_pr: openPrByRef.get(r.b)?.number ?? null,
      })), null, 2));
      break;
    }

    if (!live.length && !held.length) {
      console.log('IN FLIGHT — nothing. No branch carries an unfinished ticket number.');
    } else {
      console.log(`IN FLIGHT — ${live.length + held.length} branch(es) on unfinished tickets:\n`);
      for (const r of live) say(r);
      if (held.length) {
        console.log(`  …and ${held.length} whose branch is older than a run (${RUN_HOURS}h) but whose`);
        console.log('  claim still stands on the remote — a run reading sources for hours looks');
        console.log('  exactly like a run that died after its merge. Do not take one without reading');
        console.log('  its PR first; `ticket.mjs landed` names the ones whose PR already merged.\n');
        for (const r of held) say(r);
      }
    }
    console.log('Git cannot tell you whether a branch LANDED — everything here squash-merges,');
    console.log('so a merged branch never becomes an ancestor of dev. The PR list is the truth:');
    console.log(`  ${REPO_URL}/pulls\n`);

    if (openPr.length) {
      console.log(`OPEN PULL REQUESTS — ${openPr.length} branch(es) whose work is already up for review:\n`);
      for (const r of openPr) {
        const pr = openPrByRef.get(r.b);
        const labels = (pr.labels ?? []);
        console.log(`  ${r.t.id}  ${String(r.t.state).padEnd(9)} ${r.t.requested_by === 'owner' ? 'OWNER ' : '      '}${r.t.title}`);
        console.log(`          ↳ ${r.b}   ${age(r)}`);
        console.log(`          PR #${pr.number} is OPEN${labels.length ? ` and labelled ${labels.join(', ')}` : ''}: ${REPO_URL}/pull/${pr.number}`);
        if (labels.includes('hold')) {
          console.log(`          \`hold\` means a run PARKED it for the owner on purpose. Do not rebuild it,`);
          console.log(`          do not take the ticket, and do not delete the branch.`);
        }
        console.log('');
      }
      console.log('The branch is older than a run, so every age reading here calls it cold — but the');
      console.log('work is visible, somebody put it up, and deleting the branch would shut the pull');
      console.log('request. Read the PR before you touch the ticket.\n');
    }

    if (recoverable.length) {
      console.log(`RECOVERABLE — ${recoverable.length} branch(es) carrying work NOBODY CAN SEE:\n`);
      for (const r of recoverable) {
        console.log(`  ${r.t.id}  ${String(r.t.state).padEnd(9)} ${r.t.requested_by === 'owner' ? 'OWNER ' : '      '}${r.t.title}`);
        console.log(`          ↳ ${r.b}   ${age(r)}`);
        console.log(`          no merged PR names this ticket and no PR ever carried this branch.`);
        console.log(`          READ IT BEFORE YOU REBUILD IT:  ${REPO_URL}/compare/dev...${r.b}?expand=1\n`);
      }
      console.log('Each of these is an unfinished ticket with commits on the remote and no pull');
      console.log('request — the shape of a run cancelled before it could open one (T-1155). The');
      console.log('queue still offers the ticket, so the next run rebuilds the work unless somebody');
      console.log('reads the branch first. Open its PR, or take its reasoning into your own and');
      console.log('delete it. A branch with an OPEN pull request is not here — it is listed above.\n');
    }

    if (cold.length) {
      console.log(`Cold — finished tickets, or unclaimed branches older than a run whose work`);
      console.log(`       a merged PR accounts for (${cold.length}):`);
      for (const r of cold) {
        console.log(`  ${r.b}  (${r.t.id}, ${r.t.state}${age(r) ? ', ' + age(r) : ''})`);
      }
      console.log('  Most are leftovers whose PR merged; delete with `git push origin --delete <branch>`.\n');
    }

    // A claim with no branch behind it is the shape of an abandoned run.
    const orphans = tickets.filter((t) => ['claimed', 'review'].includes(t.state)
      && !rows.some((r) => r.t.id === t.id));
    if (orphans.length) {
      console.log(`Claimed in the merged files, with no branch on the remote (${orphans.length}) —`);
      console.log('a run that claimed and never pushed, or a branch already deleted:');
      for (const t of orphans) console.log(`  ${t.id}  ${t.title}${t.claimed_by ? `  [${t.claimed_by}]` : ''}`);
      console.log('');
    }

    const unmatched = branches.length - rows.length;
    if (unmatched > 0) console.log(`${unmatched} other branch(es) carry no ticket number (bakes, chores) — not listed.`);

    // …and the question git cannot answer, asked here because THIS is the command a
    // run reads before it picks work, and its cold list is where a finished ticket
    // hides (T-0802). Best-effort: `--no-landed` skips it, and a failure is silence.
    if (!has('no-landed')) {
      console.log('');
      // The same collection the `recoverable` reading was decided on — asked once.
      try { reportLanded(tickets, { collected: landed ?? undefined }); } catch { /* rule 3 */ }
    }
    break;
  }
  case 'landed': {
    // T-0802. The one question git cannot answer: has this ticket's PR already
    // merged? Read the closed PRs, match the ids their titles LEAD with, and report
    // every unfinished ticket that one of them names. Exit 0 whatever it finds —
    // see reportLanded, and the rules above it.
    const fixtureFile = flag('pr-json');
    let fixture = null;
    if (typeof fixtureFile === 'string') {
      // The offline demonstration: a constructed PR list, so the gate can prove this
      // fires without a network call and without waiting for a live instance.
      fixture = JSON.parse(readFileSync(fixtureFile, 'utf8'));
    }
    // `--pages N` buys a deeper horizon when the report says it did not reach the
    // oldest workable ticket. The default six is ~600 closed PRs, about a fortnight
    // of this lane, which is the window the fault actually lives in.
    const maxPages = Math.max(1, Math.min(30, Number(flag('pages')) || 6));
    const { found } = reportLanded(tickets, { fixture, maxPages });
    if (has('json')) console.log(JSON.stringify(found.map(({ t, pr }) => ({
      id: t.id, state: t.state, pr: pr.number, merged_at: pr.merged_at, pr_title: pr.title,
    })), null, 2));
    break;
  }
  case 'check': {
    const problems = check(tickets);
    if (problems.length) {
      console.error('ticket queue FAILED:');
      for (const p of problems) console.error('  - ' + p);
      process.exit(1);
    }
    const open = tickets.filter((t) => WORKABLE.includes(t.state)).length;
    const blocked = tickets.filter((t) => t.state === 'blocked-owner').length;
    console.log(`ticket queue OK — ${tickets.length} tickets, ${open} in the queue, ${blocked} waiting on the owner`);
    break;
  }
  case 'claims': {
    // The claim locks, and a broom for the ones nobody released. A stale marker
    // is never a BLOCK — the next claim steals it — so this is hygiene, and it
    // is a separate verb because deleting other runs' claims is not something
    // `check` should ever do on its way past.
    const markers = remoteBranches().filter((b) => isClaimMarker(b.name));
    if (!markers.length) { console.log('no claim locks held'); break; }
    console.log(`CLAIM LOCKS — ${markers.length} held:\n`);
    const stale = [];
    for (const m of markers) {
      const id = tickets.find((t) => branchCarries(m.name, t.id))?.id;
      const info = inspectClaim(id ?? m.name.replace(/^claim\//, '').toUpperCase());
      const dead = info.ageHours !== null && info.ageHours > RUN_HOURS;
      if (dead) stale.push(m.name);
      console.log(`  ${m.name.padEnd(18)} ${sinceWords(info.ageHours)}${dead ? '  ← older than a run' : ''}`);
      if (info.by) for (const line of info.by.split('\n').filter(Boolean)) console.log(`      ${line}`);
    }
    if (has('sweep')) {
      for (const name of stale) {
        const ok = gitTry(['push', 'origin', '--delete', name]).ok;
        console.log(`  ${ok ? 'deleted' : 'could not delete'} ${name}`);
      }
      if (!stale.length) console.log('\nnothing stale to sweep');
    } else if (stale.length) {
      console.log(`\n${stale.length} older than ${RUN_HOURS}h — \`ticket.mjs claims --sweep\` deletes those.`);
    }

    // T-1287's id locks are a different animal and are swept by a different rule.
    // A claim is a LEASE — it expires with the run, and age is what makes it stale.
    // An id reservation is not a lease: it says an id is spoken for, and it has to
    // hold from the minute a run mints until the ticket reaches `dev`, which may be
    // hours and several merges later. Age would delete it exactly when it is still
    // doing its job. So the rule is possession: once the ticket IS on the base, the
    // ticket file is the reservation and the marker is litter.
    const idLocks = remoteBranches().filter((b) => /^idlock\/t-\d{4}$/.test(b.name));
    if (idLocks.length) {
      // TWO WAYS A RESERVATION STOPS BEING ONE, and only the first was obvious.
      //
      //   landed    — the tree carries the ticket, so the ticket file IS the
      //               reservation and the marker is litter.
      //   abandoned — no tree anywhere carries it and the marker is older than a
      //               run. The mint never became a ticket: a run died between
      //               reserving and writing, or somebody probed the mechanism.
      //               Swept by AGE here because possession can never arrive —
      //               without this an abandoned lock is litter for ever, and it
      //               also burns the id, since the next mint steps past a held ref.
      const idOfLock = (b) => b.name.replace(/^idlock\//, '').toUpperCase();
      const landed = idLocks.filter((b) => tickets.some((t) => t.id === idOfLock(b)));
      const abandoned = idLocks.filter((b) => {
        if (tickets.some((t) => t.id === idOfLock(b))) return false;
        const age = branchAgeHours(b.sha);
        return age !== null && age > RUN_HOURS;
      });
      console.log(`\nID LOCKS — ${idLocks.length} held, ${landed.length} landed, ${abandoned.length} abandoned`);
      if (has('sweep')) {
        for (const b of [...landed, ...abandoned]) {
          const ok = gitTry(['push', 'origin', '--delete', b.name]).ok;
          console.log(`  ${ok ? 'deleted' : 'could not delete'} ${b.name}`);
        }
        if (!landed.length && !abandoned.length) {
          console.log('  nothing to sweep — every reservation is still in flight');
        }
      } else if (landed.length || abandoned.length) {
        console.log(`  \`ticket.mjs claims --sweep\` deletes the ${landed.length + abandoned.length} `
          + 'that are no longer reserving anything.');
      }
    }
    break;
  }
  default:
    console.log('usage: ticket.mjs new|claim|done|block|unblock|withdraw|restamp|split|list|inflight|landed|claims|prune|reconcile|board|check');
    process.exit(cmd ? 1 : 0);
}
