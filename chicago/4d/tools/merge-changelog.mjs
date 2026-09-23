#!/usr/bin/env node
/**
 * The git merge driver for renderers/web/js/changelog.js and its two mirrors.
 *
 * THE CONFLICT THIS EXISTS FOR, and it happens on nearly every branch. The
 * changelog is append-at-the-TOP, so two branches that each ship an entry both
 * insert at the same line. A text merge conflicts there every time, and the
 * conflict cuts THROUGH an entry: the shared closing `    ] },` is common
 * context, so a careless resolution leaves one entry without its close.
 *
 * WHY NOT `merge=union`, which this file used to carry. The repo's own
 * .gitattributes records what that cost: union is a LINE union and a changelog
 * entry is MANY lines, so the shared close survived once, the first entry
 * swallowed the second, and the result was still valid JavaScript — `node
 * --check` passed it — so nothing noticed until a human read the file. Five
 * merges in one day, each repaired by hand. Union was removed, and the file has
 * conflicted loudly ever since. That is better, and it is still a hand repair
 * every time: three of them on 2026-09-04 alone, each the identical edit.
 *
 * A DRIVER IS NOT UNION. Union is line-blind; this is entry-aware. It never
 * splices two entries together, because it never works below entry granularity.
 *
 *     result = OURS' NEW ENTRIES (reset to v: null, ts: '')  on top of
 *              THEIRS' ENTRIES, verbatim and in their order.
 *
 * THEIRS is the settled history — it is what is on `dev`, already stamped and
 * already numbered — so it is taken whole and never renumbered. OURS' new
 * entries are the ones being merged in, and they go on top UNSTAMPED, which is
 * exactly what the contract asks authors to write (`v: null`, `ts: ''`) and what
 * `stamp-changelog.mjs` then assigns. Two branches that each guessed "top + 1"
 * both get it wrong; the stamper is the only thing allowed to number an entry.
 *
 * SO THE MERGE IS NOT FINISHED WHEN THIS RETURNS. Run:
 *     node chicago/4d/tools/stamp-changelog.mjs
 *     node chicago/4d/tools/check-changelog.mjs
 * The driver prints that reminder on every non-trivial merge.
 *
 * IT REFUSES RATHER THAN GUESSES, in the one case union got silently wrong:
 * if both sides changed the SAME existing entry differently, or if the result
 * would carry one title twice, it exits non-zero and leaves ordinary conflict
 * markers for a human. Editing a shipped entry is rare; corrupting one is not
 * worth automating around.
 *
 * Entry identity is the TITLE, not `v`. `v` is precisely the field that
 * collides — two branches both mint the same number — so it cannot identify an
 * entry across the three versions. Titles are distinctive prose and stable.
 *
 * Registered by `tools/setup-merge-drivers.sh`; declared in .gitattributes.
 * Unregistered, git falls back to the ordinary text merge — today's behaviour,
 * never something worse.
 *
 * Usage (git calls this):  merge-changelog.mjs %O %A %B %P
 *   %O base   %A ours (READ AND WRITTEN)   %B theirs   %P path
 */
import { readFileSync, writeFileSync } from 'node:fs';

const [base, ours, theirs, label = 'changelog.js'] = process.argv.slice(2);
if (!base || !ours || !theirs) {
  console.error('usage: merge-changelog.mjs %O %A %B %P');
  process.exit(2);
}

const START = /^  \{ v: /;                 // an entry begins here, and only here
const TITLE = /title:\s*'((?:[^'\\]|\\.)*)'/;
const read = (p) => { try { return readFileSync(p, 'utf8'); } catch { return ''; } };

/**
 * Split a changelog into { prologue, entries: [{title, text}], epilogue }.
 *
 * Delimited by entry STARTS, never by the closing token: two of the 513 entries
 * on dev close on the same line as their last item (`…',    ] },`) rather than
 * on a line of their own, and a close-delimited parser silently loses them.
 */
function parse(text) {
  const lines = text.split('\n');
  const starts = [];
  lines.forEach((l, i) => { if (START.test(l)) starts.push(i); });
  if (!starts.length) return { prologue: text, entries: [], epilogue: '', ok: text.trim() === '' };
  const term = lines.findIndex((l, i) => i > starts[starts.length - 1] && l.trim() === '];');
  if (term < 0) return { ok: false, why: 'no terminating "];"' };
  const entries = starts.map((s, k) => {
    const end = (k + 1 < starts.length ? starts[k + 1] : term) - 1;
    const text_ = lines.slice(s, end + 1).join('\n');
    const t = TITLE.exec(text_);
    return { title: t ? t[1] : `«untitled@${s}»`, text: text_ };
  });
  return {
    prologue: lines.slice(0, starts[0]).join('\n'),
    entries,
    epilogue: lines.slice(term).join('\n'),
    ok: true,
  };
}

/** Reset an entry so the stamper will number and date it. */
const unstamp = (text) => text
  .replace(/^(\s*\{\s*)v:\s*[^,]+,/, '$1v: null,')
  .replace(/ts:\s*'[^']*'\s*,\s*date:\s*'[^']*'\s*,/, "ts: '',")
  .replace(/ts:\s*'[^']*'\s*,(?!\s*date:)/, "ts: '',");

const B = parse(read(base));
const O = parse(read(ours));
const T = parse(read(theirs));
const die = (msg) => { console.error(`merge-changelog: ${label} — ${msg}`); process.exit(1); };
for (const [name, p] of [['base', B], ['ours', O], ['theirs', T]]) {
  if (!p.ok) die(`could not parse ${name} (${p.why ?? 'unrecognised shape'}) — resolve by hand`);
}

const byTitle = (p) => new Map(p.entries.map((e) => [e.title, e]));
const bT = byTitle(B); const oT = byTitle(O); const tT = byTitle(T);

// REFUSE: both sides edited one existing entry differently. Union's silent case.
for (const [title, b] of bT) {
  const o = oT.get(title); const t = tT.get(title);
  if (o && t && o.text !== b.text && t.text !== b.text && o.text !== t.text) {
    die(`both sides edited the entry "${title.slice(0, 60)}" differently — resolve by hand`);
  }
}

const oursNew = O.entries.filter((e) => !bT.has(e.title) && !tT.has(e.title));
const merged = [...oursNew.map((e) => ({ ...e, text: unstamp(e.text) })), ...T.entries];

// REFUSE: a title twice is an entry duplicated, which is what we exist to prevent.
const seen = new Set(); const dupes = [];
for (const e of merged) { if (seen.has(e.title)) dupes.push(e.title); seen.add(e.title); }
if (dupes.length) die(`would carry "${dupes[0].slice(0, 60)}" twice — resolve by hand`);

const out = [T.prologue || O.prologue, ...merged.map((e) => e.text), T.epilogue || O.epilogue].join('\n');
writeFileSync(ours, out.endsWith('\n') ? out : `${out}\n`);

if (oursNew.length) {
  console.error(`merge-changelog: ${label} — ${oursNew.length} entry(s) of ours placed on top of `
    + `${T.entries.length} from theirs, UNSTAMPED. Now run:\n`
    + '  node chicago/4d/tools/stamp-changelog.mjs && node chicago/4d/tools/check-changelog.mjs');
} else {
  console.error(`merge-changelog: ${label} — nothing of ours to add; took theirs (${T.entries.length} entries).`);
}
process.exit(0);
