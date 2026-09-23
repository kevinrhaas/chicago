#!/usr/bin/env node
/**
 * resolve_id_collisions.mjs — two branches minted the same T-NNNN. Renumber the
 * one this branch added, keep the one the base already has, and carry every
 * reference this branch wrote along with it.
 *
 * WHY THIS EXISTS (measured 2026-09-10, and it is the price of running the lane
 * at more than one slice).
 *
 * `ticket.mjs nextIdNum` already scans EVERY `origin/*` ref before it mints, so
 * a collision is not a missing guard — it is the window between minting an id
 * and pushing the branch that carries it. On 2026-09-10 that window was about
 * ten minutes wide and two slices landed inside it: PR #1048 filed T-0988 (the
 * December 1835 State census) and PR #1049 filed T-0988 (Second Presbyterian's
 * 82 roll members). Both were right to think 988 was free. No scan can close
 * that window, because the fact that closes it does not exist yet.
 *
 * WHAT IT COSTS IF NOTHING HEALS IT. Merging `dev` into the second branch is
 * CLEAN — zero conflicts, git has no opinion about two files with the same
 * front-matter id. `tools/check.sh` then fails on `ticket.mjs check`:
 *
 *   T-0988-…-state-census.md: DUPLICATE id T-0988 (also T-0988-…-presbyterian.md)
 *
 * so `.github/steward/pr-lap.sh` records GATE RED, does not push, and the PR
 * keeps a head GitHub calls out of date. Auto-merge can never fire on it. The
 * branch is not wrong about anything; it is stuck on bookkeeping.
 *
 * SO A DUPLICATE ID IS BOOKKEEPING, AND THE LAP TREATS IT LIKE ONE. That is the
 * same line pr-lap.sh already draws for the files a tool owns: a conflict in
 * BOARD.md is not a disagreement about the town, so the tool rewrites it and the
 * lap moves on. A number nobody chose on purpose is the same kind of thing.
 * `ticket.mjs restamp` is the existing remedy and this only decides WHICH of the
 * pair moves and then finishes the job restamp does not do.
 *
 * THE RULE FOR WHICH ONE MOVES, and it is not "the younger":
 *
 *   the side the BASE already carries never moves.
 *
 * Whatever is on `dev` has been merged, announced in a PR body, and may already
 * be cited by another branch in flight. Renumbering it would break references
 * this run cannot even see. The side this branch ADDED is the side that moves,
 * every time, and it is identified by asking git — not by opened-date, not by
 * filename. When BOTH sides are new to the branch (one run minted twice), the
 * first by filename stays and the rest move, which is arbitrary but stated.
 * When BOTH are on the base, this REFUSES: the base is already broken and a run
 * repairing it silently is the worse outcome.
 *
 * THE HALF `restamp` DOES NOT DO. restamp renames the file, rewrites the front
 * matter and keeps the ticket's place in QUEUE.md (T-0217). It does not know
 * that the branch also wrote "T-0988 pays it down" into check.sh, into
 * research_spend_baseline.json's `why`, and into two other tickets' Links
 * lines — four references on the 2026-09-10 pair. Left alone those now point at
 * a DIFFERENT ticket, which is worse than pointing at nothing: this project's
 * own rule is that a wrong reason retires the question. So references move too.
 *
 * WHICH REFERENCES MOVE, and the loose answer is wrong. "Any line not on the
 * base" is the obvious test and it over-reaches: run it on the 2026-09-10 pair
 * and it also rewrites T-0404, whose line says T-0988 meaning the STATE CENSUS
 * ticket — the one that stays. That line is not on the base either, because it
 * arrived on a different branch. In a tree holding two T-0988s a bare mention is
 * genuinely ambiguous, so the tool asks the one question that is not:
 *
 *   the moving ticket's file was added by commit C.
 *   a reference belongs to it only if the commit that wrote that line has C as
 *   an ancestor — you cannot cite a ticket before it exists.
 *
 * T-0404's line was written on a branch where C is not an ancestor, so it stays
 * at T-0988 and stays correct. check.sh's line was written by C itself, so it
 * moves. Lines not committed yet are this run's own work and move with it.
 *
 *   node tools/resolve_id_collisions.mjs [--base origin/dev] [--check] [--self-test]
 *
 * `--check` reports and writes nothing, exiting 1 if a collision stands — that
 * is the form `tools/preflight.sh` runs before a PR is opened. With no flags it
 * repairs, which is the form the lap runs after it merges the base in.
 */
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const APP = path.resolve(HERE, '..');
const TICKETS = path.join(APP, 'tickets');

const argv = process.argv.slice(2);
const flag = (n) => {
  const i = argv.indexOf(`--${n}`);
  return i >= 0 ? (argv[i + 1] ?? '') : null;
};
const has = (n) => argv.includes(`--${n}`);
const BASE = flag('base') ?? 'origin/dev';

const git = (args, opts = {}) => execFileSync('git', args, {
  cwd: opts.cwd ?? APP, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
});
/** git that is allowed to fail — a path absent from a ref is an answer, not an error. */
const gitOr = (args, fallback = null, opts = {}) => {
  try { return git(args, opts); } catch { return fallback; }
};

/* ------------------------------------------------------------------ reading */

const idOfFile = (f) => /^id:\s*(T-\d{4})\s*$/m.exec(readFileSync(f, 'utf8'))?.[1] ?? null;
const titleOf = (f) => /^title:\s*(.*)$/m.exec(readFileSync(f, 'utf8'))?.[1]?.trim() ?? '';
const stateOf = (f) => /^state:\s*(\S+)\s*$/m.exec(readFileSync(f, 'utf8'))?.[1] ?? '';
/** The states `ticket.mjs check` expects to find in QUEUE.md, and only those. */
const WORKABLE = ['open', 'claimed', 'blocked'];

/** Every ticket file on disk, as { id, file, base } — base = its path from the repo top. */
function ticketsOnDisk(cwd = APP) {
  const dir = path.join(cwd, 'tickets');
  return readdirSync(dir)
    .filter((n) => /^T-\d{4}-.*\.md$/.test(n))
    .sort()
    .map((n) => ({ file: path.join(dir, n), name: n, id: idOfFile(path.join(dir, n)) }))
    .filter((t) => t.id);
}

/** The ticket FILENAMES the base ref carries. A name absent here is this branch's. */
function namesOnBase(cwd = APP) {
  const prefix = gitOr(['rev-parse', '--show-prefix'], '', { cwd })?.trim() ?? '';
  const top = gitOr(['rev-parse', '--show-toplevel'], null, { cwd })?.trim();
  if (!top) return null;                       // not a git tree at all
  const listing = gitOr(['ls-tree', '--name-only', `${BASE}:${prefix}tickets`], null,
    { cwd: top });
  if (listing === null) return null;           // no such ref — say so, do not guess
  return new Set(listing.split('\n').map((s) => s.trim()).filter(Boolean));
}

/* -------------------------------------------------------------- the decision */

/**
 * Group the duplicates and say, for each, which files move and which stays.
 * Returns { id, stay, move[], why } — or { id, refuse } when it must not choose.
 */
function collisions(tickets, onBase) {
  const byId = new Map();
  for (const t of tickets) {
    if (!byId.has(t.id)) byId.set(t.id, []);
    byId.get(t.id).push(t);
  }
  const out = [];
  for (const [id, group] of byId) {
    if (group.length < 2) continue;
    if (onBase === null) {
      out.push({ id, refuse: `cannot read ${BASE} — with no base to compare against there `
        + 'is no way to tell which side this branch added' });
      continue;
    }
    const fromBase = group.filter((t) => onBase.has(t.name));
    const fromBranch = group.filter((t) => !onBase.has(t.name));
    if (fromBase.length === group.length) {
      out.push({ id, refuse: `every file carrying ${id} is already on ${BASE} — the base `
        + 'itself is broken, and repairing that quietly is not this tool\'s call' });
    } else if (fromBase.length === 1) {
      out.push({ id, stay: fromBase[0], move: fromBranch,
        why: `${fromBase[0].name} is on ${BASE}` });
    } else if (fromBase.length === 0) {
      out.push({ id, stay: group[0], move: group.slice(1),
        why: `none of them is on ${BASE} — one branch minted ${id} twice, so the first by `
          + 'filename stays' });
    } else {
      out.push({ id, refuse: `${fromBase.length} of these are on ${BASE} and ${fromBranch.length} `
        + 'are not — that is not a shape this tool has a rule for' });
    }
  }
  return out;
}

/* ------------------------------------------------------- moving a reference */

/**
 * THE LINES THE BASE ALREADY HAS IN ONE FILE. Anything else was written after
 * it, and is a candidate. A file the base does not have at all is all candidate.
 *
 * Line CONTENT rather than diff hunks, deliberately. A hunk-based answer has to
 * track offsets through the edit it is about to make; a content-based one does
 * not, and the only case it gets wrong — a line written later that is
 * character-for-character identical to one already on the base — is a line where
 * both answers are the same anyway.
 */
function baseLines(relPath, top) {
  const before = gitOr(['show', `${BASE}:${relPath}`], null, { cwd: top });
  if (before === null) return null;                       // not on the base: all of it is later
  return new Set(before.split('\n'));
}

/**
 * THE COMMIT THAT ADDED A FILE — the `C` the ancestry test above is about.
 * Null when the file is not committed yet, which makes every candidate line
 * this run's own and is the right answer for a run repairing its own work.
 */
function addedBy(relPath, top) {
  const sha = gitOr(['log', '--diff-filter=A', '--format=%H', '-1', '--', relPath], '', { cwd: top });
  return sha?.trim() || null;
}

/**
 * WHO WROTE ONE LINE. `git blame` on a single line, porcelain, so the answer is
 * the sha on the first token of the first line. All-zeros means "not committed
 * yet" and is reported as null.
 */
function wroteLine(relPath, lineNo, top) {
  const out = gitOr(['blame', '--porcelain', '-L', `${lineNo},${lineNo}`, '--', relPath],
    null, { cwd: top });
  const sha = out?.split('\n')[0]?.split(' ')[0] ?? null;
  return !sha || /^0+$/.test(sha) ? null : sha;
}

/** Does `sha` stand at or after the commit that created the moving ticket? */
function citesTicket(sha, addSha, top) {
  if (sha === null) return true;          // uncommitted: this run's own line
  if (addSha === null) return true;       // the ticket is not committed either
  if (sha === addSha) return true;
  return gitOr(['merge-base', '--is-ancestor', addSha, sha], '__no__', { cwd: top }) !== '__no__';
}

/** Files under the app that mention `id`, excluding what a tool rewrites anyway. */
function mentioning(id, top) {
  const NEVER = [
    'chicago/4d/tickets/BOARD.md',       // regenerated from the tickets themselves
    'chicago/4d/tickets/tickets.json',
  ];
  const out = gitOr(['grep', '-l', '-F', id, '--', 'chicago/4d/'], '', { cwd: top }) ?? '';
  return out.split('\n').map((s) => s.trim())
    .filter(Boolean).filter((f) => !NEVER.includes(f));
}

/**
 * Rewrite `oldId` → `newId` on the lines that can only mean the MOVING ticket:
 * written after the base, by a commit standing at or after the one that created
 * it. Returns { moved, kept } — kept is the count this deliberately left alone,
 * because a reference it declined to move is worth saying out loud.
 */
function carryReferences(relPath, oldId, newId, addSha, top) {
  const abs = path.join(top, relPath);
  let text;
  try { text = readFileSync(abs, 'utf8'); } catch { return { moved: 0, kept: 0 }; }
  const onBase = baseLines(relPath, top);
  let moved = 0;
  let kept = 0;
  const next = text.split('\n').map((line, i) => {
    if (!line.includes(oldId)) return line;
    // A line the base already has is the base's own business, and there is
    // nothing interesting to report about leaving it alone.
    if (onBase && onBase.has(line)) return line;
    if (!citesTicket(wroteLine(relPath, i + 1, top), addSha, top)) {
      kept += 1;              // written where the moving ticket did not yet exist
      return line;
    }
    moved += 1;
    return line.split(oldId).join(newId);
  });
  if (moved) writeFileSync(abs, next.join('\n'));
  return { moved, kept };
}

/**
 * A CLOSED TICKET MAY NOT COME BACK INTO THE QUEUE, and restamp cannot help
 * here. Found on PR #1053, 2026-09-10, by the gate rather than by reasoning.
 *
 * That branch had filed T-0990 AND CLOSED IT in the same PR, so it has no queue
 * line of its own — a done ticket is not workable and `ticket.mjs check` refuses
 * to find one in QUEUE.md. dev's T-0990 is open and does have one, and after the
 * merge that single line was the only T-0990 in the file.
 *
 * `restamp` resolves the line to rewrite by id AND title (T-0217), then falls
 * back to the first line carrying the id when no title matches — which is
 * exactly this case, and the fallback took DEV'S line and relabelled it with the
 * branch's closed ticket. It prints a NOTE when it guesses, but only if another
 * line with the old id survives; here none did, so it was silent. The result
 * gated red: "QUEUE.md lists T-0993, which is not an open ticket (state done)".
 *
 * So the moved ticket's own state decides, after the fact and regardless of what
 * restamp did: a ticket that is not workable holds no line. The survivor's line
 * is put back separately, below, which is what repairs the theft.
 */
function dropQueueLineIfClosed(id, file, top) {
  if (WORKABLE.includes(stateOf(file))) return null;
  const prefix = git(['rev-parse', '--show-prefix'], { cwd: APP }).trim();
  const abs = path.join(top, `${prefix}tickets/QUEUE.md`);
  const rows = readFileSync(abs, 'utf8').split('\n');
  const kept = rows.filter((l) => /^(T-\d{4})\b/.exec(l.trim())?.[1] !== id);
  if (kept.length === rows.length) return null;
  writeFileSync(abs, kept.join('\n').replace(/\n+$/, '\n'));
  return `it is ${stateOf(file)}, not workable, so the line restamp gave it was removed`;
}

/* --------------------------------------------------- the queue line that dies */

/**
 * THE SURVIVOR'S QUEUE LINE, WHICH THE MERGE ITSELF EATS. Found the hard way on
 * the 2026-09-10 pair: `tools/merge-queue.mjs` reconciles QUEUE.md BY ID, so two
 * lines both saying `T-0988 — …` are one ticket as far as it can tell. It keeps
 * ours and drops theirs, and the base's ticket comes out of the merge with no
 * line at all — `ticket.mjs check` then reports it missing from the queue, which
 * is a second red on top of the duplicate and is not the branch's fault either.
 *
 * Appending it would clear the red and is exactly the wrong repair: QUEUE.md is
 * ordered by the owner, the survivor sat inside a band, and the bottom of the
 * file is the epics. So it goes back UNDER THE TICKET IT FOLLOWED ON THE BASE —
 * the same rule `ticket.mjs new --after` follows, and placing is not reordering.
 * If that predecessor is gone from the queue too, this walks further up the
 * base's order until it finds one that is still there.
 */
function restoreQueueLine(id, title, top) {
  const prefix = git(['rev-parse', '--show-prefix'], { cwd: APP }).trim();
  const rel = `${prefix}tickets/QUEUE.md`;
  const abs = path.join(top, rel);
  const idOfLine = (l) => /^(T-\d{4})\b/.exec(l.trim())?.[1] ?? null;

  const now = readFileSync(abs, 'utf8').split('\n');
  if (now.some((l) => idOfLine(l) === id)) return null;            // still there

  const baseQueue = gitOr(['show', `${BASE}:${rel}`], null, { cwd: top });
  const line = `${id} — ${title}`;
  const present = new Set(now.map(idOfLine).filter(Boolean));

  if (baseQueue) {
    const rows = baseQueue.split('\n');
    const at = rows.findIndex((l) => idOfLine(l) === id);
    for (let i = at - 1; i >= 0; i -= 1) {
      const anchor = idOfLine(rows[i]);
      if (!anchor || !present.has(anchor)) continue;
      const into = now.findIndex((l) => idOfLine(l) === anchor);
      now.splice(into + 1, 0, line);
      writeFileSync(abs, now.join('\n').replace(/\n+$/, '\n'));
      return `restored under ${anchor}, the ticket it followed on ${BASE}`;
    }
  }
  now.push(line);
  writeFileSync(abs, now.join('\n').replace(/\n+$/, '\n'));
  return 'APPENDED at the bottom — nothing it followed on the base is still in the '
    + 'queue, so its band could not be found; the owner should move it';
}

/* ---------------------------------------------------------------- the repair */

function run() {
  const tickets = ticketsOnDisk();
  const onBase = namesOnBase();
  const found = collisions(tickets, onBase);

  if (found.length === 0) {
    console.log(`ticket ids: no collision — ${tickets.length} tickets, every id unique`);
    return 0;
  }

  const refusals = found.filter((c) => c.refuse);
  const repairs = found.filter((c) => !c.refuse);

  for (const c of refusals) {
    console.error(`ticket ids: ${c.id} REFUSED — ${c.refuse}`);
  }

  if (has('check')) {
    for (const c of repairs) {
      console.error(`ticket ids: ${c.id} is carried by ${c.move.length + 1} files — `
        + `${c.stay.name} stays (${c.why}), ${c.move.map((m) => m.name).join(', ')} would move`);
    }
    console.error('\nRun `node tools/resolve_id_collisions.mjs` to renumber the side this '
      + 'branch added and carry its references with it.');
    return 1;
  }

  const top = git(['rev-parse', '--show-toplevel']).trim();
  for (const c of repairs) {
    console.log(`ticket ids: ${c.id} — ${c.stay.name} stays (${c.why})`);
    for (const m of c.move) {
      // ASKED BEFORE THE RESTAMP, because restamp renames the file out from under
      // it and `git log -- <path>` would then have nothing to answer about.
      const addSha = addedBy(path.relative(top, m.file), top);
      // restamp owns the ticket file, its front matter and its QUEUE.md line.
      const said = execFileSync('node', [path.join(APP, 'tools', 'ticket.mjs'), 'restamp', m.file],
        { cwd: APP, encoding: 'utf8' });
      const newId = /T-\d{4}\s*→\s*(T-\d{4})/.exec(said)?.[1];
      if (!newId) {
        console.error(`ticket ids: restamp did not report a new id for ${m.name}:\n${said}`);
        return 1;
      }
      let carried = 0;
      let left = 0;
      const touched = [];
      for (const rel of mentioning(c.id, top)) {
        const { moved, kept } = carryReferences(rel, c.id, newId, addSha, top);
        left += kept;
        if (moved) { carried += moved; touched.push(`${rel} (${moved})`); }
      }
      // BEFORE the survivor's line is restored, because restamp may have handed
      // this ticket the survivor's own line (see dropQueueLineIfClosed). restamp
      // renamed the file, so it is found again by the id it now carries rather
      // than by reconstructing a slug this tool does not own.
      const moved = ticketsOnDisk().find((t) => t.id === newId);
      const dropped = moved ? dropQueueLineIfClosed(newId, moved.file, top) : null;
      console.log(`  ${m.name}\n    → ${newId}${dropped ? '' : ', queue place kept'}`);
      if (dropped) console.log(`    no queue line — ${dropped}`);
      console.log(`    ${carried} reference line(s) carried with it`
        + (touched.length ? `: ${touched.join(', ')}` : ''));
      if (left) {
        console.log(`    ${left} line(s) left at ${c.id} — they were written before `
          + 'this ticket existed, so they mean the one that stays');
      }
    }
    // Only now, with the duplicate gone from QUEUE.md, can the survivor's own
    // line go back: while both said T-0988 the queue could not hold them apart.
    const restored = restoreQueueLine(c.id, titleOf(c.stay.file), top);
    if (restored) console.log(`    ${c.stay.name}'s queue line was eaten by the merge — ${restored}`);
  }
  return refusals.length ? 1 : 0;
}

/* -------------------------------------------------------------- self-test */

async function selfTest() {
  const { mkdtempSync, mkdirSync, rmSync, cpSync } = await import('node:fs');
  const { tmpdir } = await import('node:os');
  let failures = 0;
  const check = (what, ok, detail) => {
    console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
    if (!ok) failures += 1;
  };

  const front = (id, title, state = 'open') => `---
id: ${id}
title: ${title}
state: ${state}
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

  /**
   * A REAL TWO-COMMIT GIT TREE, because the whole question this tool answers is
   * "which side did the branch add", and that is a question only git can answer.
   * A fixture of loose files would let the test pass while the tool guessed.
   */
  const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-collide-'));
  const APPX = path.join(tmp, 'chicago', '4d');
  const T = path.join(APPX, 'tickets');
  const G = (...a) => execFileSync('git', a, { cwd: tmp, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  try {
    mkdirSync(path.join(APPX, 'tools'), { recursive: true });
    mkdirSync(T, { recursive: true });
    for (const f of ['ticket.mjs', 'resolve_id_collisions.mjs']) {
      cpSync(path.join(APP, 'tools', f), path.join(APPX, 'tools', f));
    }
    G('init', '-q', '-b', 'main');
    G('config', 'user.email', 't@t'); G('config', 'user.name', 't');

    // --- the base: T-0001 sitting INSIDE a band under an anchor, plus a tool
    // file that cites it. The anchor is the point: when the merge eats T-0001's
    // line, the repair has to put it back here and not at the bottom.
    writeFileSync(path.join(T, 'T-0001-base-ticket.md'), front('T-0001', 'The base ticket'));
    writeFileSync(path.join(T, 'T-0009-anchor.md'), front('T-0009', 'The anchor above it'));
    writeFileSync(path.join(T, 'T-0008-last.md'), front('T-0008', 'A ticket ranked below'));
    writeFileSync(path.join(T, 'QUEUE.md'),
      '# QUEUE — top is next.\n\nT-0009 — The anchor above it\nT-0001 — The base ticket\n'
      + 'T-0008 — A ticket ranked below\n');
    writeFileSync(path.join(APPX, 'tools', 'notes.md'),
      'The base wrote this line about T-0001 and it must not move.\n');
    G('add', '-A'); G('commit', '-qm', 'base');
    G('branch', 'base-ref');

    // --- a SIBLING branch, off the same base, that cites T-0001 meaning the
    // BASE's ticket. This is the T-0404 case from 2026-09-10: its line is not on
    // the base either, so "not on the base" would wrongly move it.
    G('checkout', '-q', '-b', 'sibling', 'base-ref');
    writeFileSync(path.join(APPX, 'tools', 'sibling.md'),
      'A sibling branch cites T-0001 meaning the base ticket, and it must NOT move.\n');
    G('add', '-A'); G('commit', '-qm', 'sibling');

    // --- the branch: mints T-0001 AGAIN, and writes two references to its own.
    G('checkout', '-q', 'main');
    writeFileSync(path.join(T, 'T-0001-branch-ticket.md'), front('T-0001', 'The branch ticket'));
    // AS THE MERGE LEAVES IT: merge-queue.mjs reconciles by id, so the two
    // T-0001 lines came out as one — ours — and the base's line is simply gone.
    writeFileSync(path.join(T, 'QUEUE.md'),
      '# QUEUE — top is next.\n\nT-0009 — The anchor above it\nT-0001 — The branch ticket\n'
      + 'T-0008 — A ticket ranked below\n');
    writeFileSync(path.join(APPX, 'tools', 'notes.md'),
      'The base wrote this line about T-0001 and it must not move.\n'
      + 'The branch wrote this line about T-0001 and it must follow.\n');
    writeFileSync(path.join(APPX, 'tools', 'added.md'),
      'A file the base does not have at all, citing T-0001.\n');
    G('add', '-A'); G('commit', '-qm', 'branch');
    G('merge', '-q', 'sibling', '--no-edit');

    const tool = (...a) => execFileSync('node',
      [path.join(APPX, 'tools', 'resolve_id_collisions.mjs'), '--base', 'base-ref', ...a],
      { cwd: APPX, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });

    console.log('\n  --check reports without writing');
    let out = '';
    let code = 0;
    try { out = tool('--check'); } catch (e) { code = e.status; out = `${e.stdout}${e.stderr}`; }
    check('exits non-zero while a collision stands', code === 1, `exit ${code}`);
    check('names the side that stays and why', /T-0001-base-ticket\.md stays/.test(out), out.trim());
    check('and wrote nothing', G('status', '--porcelain').trim() === '');

    console.log('\n  the repair');
    out = tool();
    const newId = /→ (T-\d{4})/.exec(out)?.[1];
    check('the BRANCH ticket is the one renumbered, to a free id',
      /^T-\d{4}$/.test(newId ?? '') && newId !== 'T-0001', out.trim());
    check('the base ticket keeps its id and its file name',
      idOfFile(path.join(T, 'T-0001-base-ticket.md')) === 'T-0001');
    check('the branch ticket file is renamed to its new id',
      idOfFile(path.join(T, `${newId}-the-branch-ticket.md`)) === newId);

    const notes = readFileSync(path.join(APPX, 'tools', 'notes.md'), 'utf8');
    check('the reference the BRANCH wrote follows it',
      notes.includes(`The branch wrote this line about ${newId}`), notes.trim());
    check('…and the reference the BASE wrote is untouched',
      /The base wrote this line about T-0001/.test(notes), notes.trim());
    check('a file the base does not have is treated as all the branch\'s',
      readFileSync(path.join(APPX, 'tools', 'added.md'), 'utf8').includes(newId));

    // THE ONE THE LOOSE RULE GETS WRONG. Written after the base, so "not on the
    // base" would move it; written where the moving ticket does not exist, so it
    // can only mean the ticket that stays.
    const sib = readFileSync(path.join(APPX, 'tools', 'sibling.md'), 'utf8');
    check('a SIBLING branch\'s reference stays at the old id — it predates the moving ticket',
      /cites T-0001 meaning the base ticket/.test(sib), sib.trim());
    check('…and the run SAYS it left it, so a declined rewrite is never silent',
      /line\(s\) left at T-0001/.test(out), out.trim());

    const q = readFileSync(path.join(T, 'QUEUE.md'), 'utf8');
    check('the branch\'s line is renumbered where it already stood',
      q.includes(`${newId} — The branch ticket`), q.trim());
    check('the survivor\'s line, eaten by the merge, is restored UNDER ITS BASE ANCHOR '
      + 'and not appended to the bottom',
      /T-0009 — The anchor above it\nT-0001 — The base ticket/.test(q)
      && /T-0008 — A ticket ranked below/.test(q.split('T-0001 — The base ticket')[1] ?? ''),
      q.trim());
    check('and the run says the merge ate it, rather than restoring it silently',
      /queue line was eaten by the merge/.test(out), out.trim());

    console.log('\n  it is idempotent, and says so');
    out = tool();
    check('a second run finds nothing to do', /no collision/.test(out), out.trim());

    // --- PR #1053's shape, which the gate caught and this had got wrong: the
    // branch FILED AND CLOSED its ticket in the same PR, so it has no queue line
    // of its own, and the single surviving line is the SURVIVOR'S. restamp's
    // resolve-by-id fallback relabels that line with the closed ticket, silently.
    console.log('\n  the moving ticket was closed in the same branch that filed it');
    writeFileSync(path.join(T, 'T-0005-base-open.md'), front('T-0005', 'The open one on the base'));
    writeFileSync(path.join(T, 'QUEUE.md'),
      readFileSync(path.join(T, 'QUEUE.md'), 'utf8').replace(/\n*$/, '\n')
      + 'T-0005 — The open one on the base\n');
    G('add', '-A'); G('commit', '-qm', 'base gains T-0005');
    G('branch', '-f', 'base-ref', 'HEAD');
    writeFileSync(path.join(T, 'T-0005-branch-done.md'),
      front('T-0005', 'The one this branch filed and closed', 'done'));
    G('add', '-A'); G('commit', '-qm', 'branch files and closes its own T-0005');

    out = tool();
    const newClosed = /→ (T-\d{4})/.exec(out)?.[1];
    const q2 = readFileSync(path.join(T, 'QUEUE.md'), 'utf8');
    check('a ticket that is `done` gets NO queue line, whatever restamp did with one',
      !q2.includes(newClosed), `${newClosed} in queue: ${q2.includes(newClosed)}`);
    check('…and the open survivor keeps its line rather than losing it to the closed one',
      /T-0005 — The open one on the base/.test(q2), q2.trim());
    check('…and the run says the line was removed, rather than removing it silently',
      /not workable, so the line restamp gave it was removed/.test(out), out.trim());

    console.log('\n  it refuses rather than guess');
    // Both sides on the base: the base is broken and this may not choose.
    writeFileSync(path.join(T, 'T-0003-a.md'), front('T-0003', 'A'));
    writeFileSync(path.join(T, 'T-0003-b.md'), front('T-0003', 'B'));
    G('add', '-A'); G('commit', '-qm', 'two on base');
    G('branch', '-f', 'base-ref', 'HEAD');
    code = 0;
    try { out = tool(); } catch (e) { code = e.status; out = `${e.stdout}${e.stderr}`; }
    check('both sides already on the base is a REFUSAL, not a coin toss',
      code === 1 && /REFUSED/.test(out) && /base itself is broken/.test(out), out.trim());
    check('and it renumbered neither of them',
      idOfFile(path.join(T, 'T-0003-a.md')) === 'T-0003'
      && idOfFile(path.join(T, 'T-0003-b.md')) === 'T-0003');
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }

  console.log(`\n${failures === 0 ? 'id-collision self-test: all pass'
    : `id-collision self-test: ${failures} FAILURE(S)`}`);
  return failures === 0 ? 0 : 1;
}

process.exit(has('self-test') ? await selfTest() : run());
