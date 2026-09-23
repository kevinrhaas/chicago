#!/usr/bin/env node
/**
 * The git merge driver for tickets/QUEUE.md.
 *
 * WHY A DRIVER AND NOT `merge=union`. The changelog tried union and the repo's
 * own .gitattributes records what it cost: union is a LINE union, a changelog
 * entry is many lines, and the shared closing bracket survived once, so one
 * entry swallowed the next and produced valid JavaScript nobody noticed. Five
 * merges in one day, each repaired by hand.
 *
 * QUEUE.md is line-structured — one ticket is exactly one line — so union would
 * not corrupt it silently the way it corrupted the changelog, and `ticket.mjs
 * check` catches every union failure mode loudly (`lists X twice`, `is not an
 * open ticket`, `missing from QUEUE.md`). But loud is not the same as resolved:
 * on the case that actually hurts — one side re-ranks the file while the other
 * closes tickets — union concatenates BOTH orderings and hands back ~300 lines
 * with every ticket twice. That is a conflict wearing a merge's clothes.
 *
 * WHAT THIS DOES INSTEAD, and it is the reconciliation done by hand four times
 * on 2026-09-04 while landing one queue re-rank:
 *
 *   result = OURS,  minus every ticket THEIRS removed since the base,
 *                   plus  every ticket THEIRS added since the base.
 *
 * OURS keeps the ORDER, because order is the owner's and the branch being merged
 * into is the one holding his instruction. THEIRS contributes membership, because
 * a ticket dev closed is closed and a ticket dev filed is real. The two sides
 * change different things about this file almost every time — one re-ranks, the
 * other opens and closes — which is exactly why a set reconciliation works where
 * a text merge cannot.
 *
 * IT REFUSES RATHER THAN GUESSES. If the result would carry a duplicate id, the
 * driver exits non-zero and git leaves the normal conflict markers for a human.
 * A queue with a ticket in it twice is a ranking nobody can read.
 *
 * Registered by `tools/setup-merge-drivers.sh` (merge.queue.driver), declared in
 * the repo's .gitattributes. If the driver is NOT registered, git falls back to
 * the ordinary text merge and you get conflict markers — the old behaviour, never
 * something worse. `check.sh` says so when it notices.
 *
 * Usage (git calls this, you do not):  merge-queue.mjs %O %A %B %P
 *   %O base   %A ours (READ AND WRITTEN — the result goes here)   %B theirs   %P path
 */
import { readFileSync, writeFileSync } from 'node:fs';

const [base, ours, theirs, label = 'QUEUE.md'] = process.argv.slice(2);
if (!base || !ours || !theirs) {
  console.error('usage: merge-queue.mjs %O %A %B %P');
  process.exit(2);
}

const TICKET = /^(T-\d{4})\b/;
const read = (p) => {
  try { return readFileSync(p, 'utf8'); } catch { return ''; }
};
/** id -> the whole line, for every ticket line in a version of the file. */
const index = (text) => {
  const m = new Map();
  for (const line of text.split('\n')) {
    const hit = TICKET.exec(line);
    if (hit) m.set(hit[1], line.replace(/\s+$/, ''));
  }
  return m;
};

const baseText = read(base);
const oursText = read(ours);
const theirsText = read(theirs);

const B = index(baseText);
const O = index(oursText);
const T = index(theirsText);

const closedByThem = [...B.keys()].filter((id) => !T.has(id));
const addedByThem = [...T.keys()].filter((id) => !B.has(id));

/**
 * WHICH SIDE'S ORDER WINS, and this is the question the first version got wrong.
 *
 * It ordered on "OURS keeps the order", reasoning that the branch being merged into
 * is the one holding the owner's instruction. That is true when ours is the newer
 * work. It is FALSE, and destructively so, when a long-stale branch merges dev: then
 * "ours" is the branch that predates the owner's re-rank, its old order wins, and the
 * moment that branch merges the old order is carried back onto dev.
 *
 * That happened on 2026-09-04. Four PRs cut before a research-first re-rank each
 * merged dev; each kept its own stale order; and the owner's ranking was gone from
 * dev by the fourth — "the queue got massively reordered, we were working on all of
 * the research items first".
 *
 * The honest rule is not about which side is "ours". It is about WHICH SIDE ACTUALLY
 * RE-ORDERED. Compare the relative sequence of the ids all three versions share:
 *   - only ours moved them   -> ours ordered deliberately; keep ours.
 *   - only theirs moved them -> theirs ordered deliberately; keep theirs.
 *   - neither moved them     -> no disagreement; keep ours (identical anyway).
 *   - BOTH moved them        -> two deliberate rankings; REFUSE and let a human read.
 */
const seq = (m) => [...m.keys()].filter((id) => B.has(id) && T.has(id) && O.has(id));
const sameOrder = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);
const baseSeq = seq(B); const oursSeq = seq(O); const theirsSeq = seq(T);
const oursReordered = !sameOrder(baseSeq, oursSeq);
const theirsReordered = !sameOrder(baseSeq, theirsSeq);
if (oursReordered && theirsReordered) {
  console.error(`merge-queue: ${label} — BOTH sides re-ranked the queue since the merge base. `
    + 'Two deliberate orderings cannot be merged mechanically; resolve by hand and keep the '
    + "one the owner asked for. (This refuses rather than silently picking a side — picking "
    + 'one is how a stale branch erased a re-rank on 2026-09-04.)');
  process.exit(1);
}
// The side that did the re-ranking supplies the file we walk; the other supplies membership.
const orderingText = theirsReordered ? theirsText : oursText;

// Walk the ordering side line by line so every comment, band header and blank line
// survives exactly where the owner put it. Only ticket lines are filtered.
const dropped = theirsReordered
  ? [...B.keys()].filter((id) => !O.has(id))     // what OURS closed
  : closedByThem;
const out = [];
for (const line of orderingText.split('\n')) {
  const hit = TICKET.exec(line);
  if (hit && dropped.includes(hit[1])) continue;
  out.push(line);
}

/**
 * A NEW TICKET IS PLACED WHERE ITS OWN SIDE PLACED IT, AND IT BRINGS ITS BAND.
 *
 * This is the T-0817 / #909 repair, and the bug it fixes was not in the ordering
 * rule above — it was here.
 *
 * Every new ticket used to be appended at the END under "MERGED IN, NOT YET
 * PLACED", and the comment lines above it were not carried at all, because only
 * the ORDERING side's text is walked. So a re-rank that arrives as "a new band,
 * with new tickets under it, at the TOP" loses both halves: the band is dropped
 * because it is a comment on the non-ordering side, and its tickets sink to the
 * bottom because they are new.
 *
 * Worse, such a re-rank does not even register as a re-rank. `seq()` compares
 * only the ids all THREE versions share, and brand-new tickets are in none of
 * them — so `theirsReordered` stays false, ours becomes the ordering side, and
 * the owner's ranking is discarded without the "both sides re-ranked" refusal
 * ever being reached. #909 measured the result: "it has now been stripped THREE
 * times ... which is how six tickets the owner put at the top of QUEUE.md came to
 * be sitting at line 416."
 *
 * So a new ticket is anchored: it goes immediately before the first ticket that
 * FOLLOWS it on its own side and also survives into the result, carrying the
 * comment lines that introduced it. Placed at the top on its own side, it lands
 * at the top here. Only a ticket with no such anchor — one genuinely appended at
 * the end — falls through to the MERGED-IN band, which is what that band was
 * always for.
 */
const lineage = (text) => {
  // For each ticket: the comment/blank lines that introduce it, and the ids that
  // follow it, in order. Comments attach downward, which is how the file reads.
  const rows = []; let lead = [];
  for (const line of text.split('\n')) {
    const hit = TICKET.exec(line);
    if (hit) { rows.push({ id: hit[1], line: line.replace(/\s+$/, ''), lead }); lead = []; }
    else lead.push(line);
  }
  return rows;
};

const present = new Set(out.map((l) => TICKET.exec(l)?.[1]).filter(Boolean));
const newIds = new Set([...new Set([...addedByThem, ...[...O.keys()].filter((id) => !B.has(id))])]
  .filter((id) => !present.has(id)));

// Each new id's own side: theirs added it unless ours did.
const sideOf = (id) => (T.has(id) && !B.has(id) ? theirsText : oursText);
const anchored = new Map();          // anchor id -> [{lead, line}, …] to insert before it
const unplaced = [];
for (const id of [...newIds]) {
  const rows = lineage(sideOf(id));
  const at = rows.findIndex((r) => r.id === id);
  const anchor = at === -1 ? undefined
    : rows.slice(at + 1).find((r) => present.has(r.id) && !dropped.includes(r.id));
  if (!anchor) { unplaced.push(id); continue; }
  if (!anchored.has(anchor.id)) anchored.set(anchor.id, []);
  anchored.get(anchor.id).push(rows[at]);
}

const placed = [];
for (const line of out) {
  const hit = TICKET.exec(line);
  for (const row of (hit && anchored.get(hit[1])) || []) {
    // Carry the band, minus any line already standing in the result — a shared
    // header must not be duplicated just because both sides carry it.
    const seenLines = new Set(placed);
    for (const l of row.lead) {
      if (l.trim() === '' || !seenLines.has(l)) placed.push(l);
    }
    placed.push(row.line);
  }
  placed.push(line);
}
out.length = 0; out.push(...placed);

// What is left really was appended at the end of its own side: the MERGED-IN band
// is for those and only those, which is what it always claimed to be.
if (unplaced.length) {
  while (out.length && !out[out.length - 1].trim()) out.pop();
  out.push('');
  out.push('# --- MERGED IN, NOT YET PLACED. These arrived on the branch being merged and were');
  out.push('# --- appended here rather than guessed into a band. Rank them or leave them.');
  for (const id of unplaced.sort()) out.push(T.get(id) ?? O.get(id));
}
out.push('');

const merged = out.join('\n').replace(/\n{3,}$/, '\n');

// The one thing worth refusing over.
const ids = merged.split('\n').map((l) => TICKET.exec(l)?.[1]).filter(Boolean);
const dupes = [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))];
if (dupes.length) {
  console.error(`merge-queue: ${label} would carry ${dupes.join(', ')} twice — refusing, `
    + 'resolve by hand. A queue with a ticket in it twice is a ranking nobody can read.');
  process.exit(1);
}

/**
 * AND THE OTHER: A BAND THE NON-ORDERING SIDE WROTE MAY NOT VANISH.
 *
 * The anchoring above carries the comment lines that introduce a NEW ticket. It
 * cannot carry a band written above an ticket that already existed — that band
 * lives only in the non-ordering side's text, and nothing walks that text.
 *
 * That is the residue of the same fault, and the file's own history says what to
 * do about it: "A driver that silently discards the owner's ranking is worse than
 * one that refuses" (#909, on the third strip). So the driver checks its own
 * work. Any comment line that the non-ordering side ADDED since the base, and
 * that is not in the result, stops the merge and is named.
 *
 * Only lines the other side ADDED count. A comment present in the base and
 * removed by the ordering side is a deliberate deletion, not a loss, and refusing
 * on those would make every tidy-up a conflict.
 */
const commentsOf = (text) => text.split('\n')
  .filter((l) => l.trimStart().startsWith('#')).map((l) => l.replace(/\s+$/, ''));
const otherText = theirsReordered ? oursText : theirsText;
const otherSide = theirsReordered ? 'ours' : 'theirs';
const inBase = new Set(commentsOf(baseText));
const inResult = new Set(commentsOf(merged));
const lostBands = [...new Set(commentsOf(otherText))]
  .filter((l) => l.trim() !== '#' && !inBase.has(l) && !inResult.has(l));
if (lostBands.length) {
  console.error(`merge-queue: ${label} — ${lostBands.length} comment line(s) that ${otherSide} `
    + 'ADDED since the merge base would be dropped by this merge. Refusing.\n');
  for (const l of lostBands.slice(0, 8)) console.error(`   would lose:  ${l.slice(0, 120)}`);
  if (lostBands.length > 8) console.error(`   …and ${lostBands.length - 8} more`);
  console.error('\nThe owner writes his ranking instructions INTO these bands, so losing them '
    + 'loses\nthe ranking. Resolve by hand: keep the band, and put its tickets where it says.\n'
    + 'A driver that silently discards the owner\'s ranking is worse than one that refuses '
    + '(#909,\nwhich recorded the third time this happened).');
  process.exit(1);
}

writeFileSync(ours, merged);
const note = [];
if (closedByThem.length) note.push(`-${closedByThem.length} closed`);
if (newIds.size) note.push(`+${newIds.size} new`);
console.error(`merge-queue: ${label} reconciled — ${theirsReordered ? "theirs'" : "ours'"} order kept`
  + (note.length ? `, ${note.join(', ')}` : ', no membership change')
  + `, ${ids.length} queued.`);
process.exit(0);
