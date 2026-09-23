#!/usr/bin/env node
/**
 * The QUEUE.md merge driver's assertions, and proof they still fire when broken.
 *
 * Every case here is one that actually happened while landing a queue re-rank on
 * 2026-09-04 — four merges, four hand reconciliations. They are the reason the
 * driver exists, so they are the reason it is tested.
 */
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const DRIVER = path.join(HERE, 'merge-queue.mjs');

let pass = 0; let fail = 0;
const ok = (cond, what) => { if (cond) { pass++; console.log(`  ok    ${what}`); } else { fail++; console.log(`  FAIL  ${what}`); } };

/** Run the driver over three versions; returns { code, text }. */
function run(base, ours, theirs) {
  const dir = mkdtempSync(path.join(tmpdir(), 'mq-'));
  const O = path.join(dir, 'base'); const A = path.join(dir, 'ours'); const B = path.join(dir, 'theirs');
  writeFileSync(O, base); writeFileSync(A, ours); writeFileSync(B, theirs);
  // spawnSync, not execFileSync: the driver reports on STDERR, and some assertions
  // check that a refusal NAMES what it refused over. A helper that throws stderr
  // away cannot test the message, and a test that cannot fail is not a test.
  const p = spawnSync('node', [DRIVER, O, A, B, 'QUEUE.md'], { encoding: 'utf8' });
  const code = p.status ?? 1;
  const log = `${p.stderr ?? ''}${p.stdout ?? ''}`;
  const text = readFileSync(A, 'utf8');
  rmSync(dir, { recursive: true, force: true });
  return { code, text, log };
}
const ids = (t) => t.split('\n').map((l) => /^(T-\d{4})\b/.exec(l)?.[1]).filter(Boolean);

const HEAD = '# QUEUE — top is next.\n# --- a band the owner wrote\n';

console.log('\n\x1b[1m== the QUEUE.md merge driver\x1b[0m');

// 1. The everyday case: they closed one, we did nothing to it.
{
  const base = HEAD + 'T-0001 — a\nT-0002 — b\nT-0003 — c\n';
  const ours = base;
  const theirs = HEAD + 'T-0001 — a\nT-0003 — c\n';
  const r = run(base, ours, theirs);
  ok(r.code === 0, 'a ticket they closed is dropped');
  ok(!ids(r.text).includes('T-0002'), '...and it is really gone');
  ok(ids(r.text).join() === 'T-0001,T-0003', '...leaving the rest in our order');
}

// 2. They filed a new one while we re-ranked.
{
  const base = HEAD + 'T-0001 — a\nT-0002 — b\n';
  const ours = HEAD + 'T-0002 — b\nT-0001 — a\n';           // we re-ranked
  const theirs = HEAD + 'T-0001 — a\nT-0002 — b\nT-0009 — new\n';
  const r = run(base, ours, theirs);
  ok(r.code === 0, 'a ticket they filed is appended');
  ok(ids(r.text).slice(0, 2).join() === 'T-0002,T-0001', "...and OUR re-rank survives it");
  ok(ids(r.text).includes('T-0009'), '...with theirs at the end');
  ok(/NOT YET PLACED/.test(r.text), '...under a band saying it is unranked');
}

// 3. THE CASE THAT MOTIVATED THE DRIVER: we re-rank the whole file, they close
//    two and file two. A text merge conflicts on every hunk; union doubles it.
{
  const base = HEAD + [1, 2, 3, 4, 5].map((n) => `T-000${n} — t${n}`).join('\n') + '\n';
  const ours = HEAD + '# --- a new band\n' + [5, 3, 1, 4, 2].map((n) => `T-000${n} — t${n}`).join('\n') + '\n';
  const theirs = HEAD + 'T-0001 — t1\nT-0003 — t3\nT-0005 — t5\nT-0008 — t8\nT-0009 — t9\n';
  const r = run(base, ours, theirs);
  ok(r.code === 0, 'a whole-file re-rank against closes and files resolves');
  ok(ids(r.text).slice(0, 3).join() === 'T-0005,T-0003,T-0001', "...our order kept for what survives");
  ok(!ids(r.text).includes('T-0002') && !ids(r.text).includes('T-0004'), '...their two closes applied');
  ok(ids(r.text).includes('T-0008') && ids(r.text).includes('T-0009'), '...their two new tickets carried');
  ok(new Set(ids(r.text)).size === ids(r.text).length, '...and nothing is duplicated');
}

// 4. Comments and bands are the owner's and must survive verbatim.
{
  const base = HEAD + 'T-0001 — a\n';
  const ours = HEAD + '# --- a band explaining why\nT-0001 — a\n';
  const theirs = HEAD + 'T-0001 — a\nT-0002 — b\n';
  const r = run(base, ours, theirs);
  ok(/a band explaining why/.test(r.text), "our band comment survives the merge");
  ok(/a band the owner wrote/.test(r.text), '...and so does the header');
}

// 5. Both sides file the SAME id — the collision this cannot paper over.
{
  const base = HEAD + 'T-0001 — a\n';
  const ours = HEAD + 'T-0001 — a\nT-0007 — ours\n';
  const theirs = HEAD + 'T-0001 — a\nT-0007 — theirs\n';
  const r = run(base, ours, theirs);
  ok(r.code === 0, 'the same id on both sides does not duplicate');
  ok(ids(r.text).filter((i) => i === 'T-0007').length === 1, '...it appears once');
  ok(/ours/.test(r.text), '...and ours is the copy kept');
}

// 6. …and its own assertions still fire when broken.
// 7. THE REGRESSION THAT COST AN OWNER HIS RANKING, 2026-09-04. A STALE branch merges
//    dev after the owner re-ranked. Ours is older; theirs carries the re-rank. The first
//    version of this driver kept OURS and erased the ranking — four times, then carried
//    the stale order back to dev on merge.
{
  const base = HEAD + [1,2,3,4].map((n) => `T-000${n} — t${n}`).join('\n') + '\n';
  const ours = base;                                            // stale: never re-ranked
  const theirs = HEAD + '# --- the owner\'s new band\n'
    + [4,3,2,1].map((n) => `T-000${n} — t${n}`).join('\n') + '\n';   // dev: re-ranked
  const r = run(base, ours, theirs);
  ok(r.code === 0, 'a stale branch merging a re-ranked dev resolves');
  ok(ids(r.text).join() === 'T-0004,T-0003,T-0002,T-0001', "...THEIRS' re-rank survives, not ours");
  ok(/the owner's new band/.test(r.text), '...and their band comment comes with it');
}

// 8. The mirror of it: we re-ranked, dev did not. Ours must win.
{
  const base = HEAD + [1,2,3,4].map((n) => `T-000${n} — t${n}`).join('\n') + '\n';
  const ours = HEAD + [4,3,2,1].map((n) => `T-000${n} — t${n}`).join('\n') + '\n';
  const theirs = HEAD + [1,2,3,4].map((n) => `T-000${n} — t${n}`).join('\n')
    + '\nT-0009 — they filed one\n';
  const r = run(base, ours, theirs);
  ok(r.code === 0, 'we re-ranked and dev did not — ours wins');
  ok(ids(r.text).slice(0,4).join() === 'T-0004,T-0003,T-0002,T-0001', '...our order kept');
  ok(ids(r.text).includes('T-0009'), '...and their new ticket still arrives');
}

console.log('\n\x1b[1m== …and the refusal still fires\x1b[0m');
{
  // A base that already carries a duplicate forces the result to carry one too.
  const base = HEAD + 'T-0001 — a\n';
  const ours = HEAD + 'T-0001 — a\nT-0001 — a again\n';
  const theirs = HEAD + 'T-0001 — a\n';
  const r = run(base, ours, theirs);
  ok(r.code !== 0, 'a result that would carry an id twice is REFUSED, not written');
}
{
  const r = run('', '', '');
  ok(r.code === 0, 'three empty files are not an error');
}

{
  // BOTH sides re-ranked: two deliberate orderings, and neither may be picked silently.
  const base = HEAD + [1,2,3,4].map((n) => `T-000${n} — t${n}`).join('\n') + '\n';
  const ours = HEAD + [4,3,2,1].map((n) => `T-000${n} — t${n}`).join('\n') + '\n';
  const theirs = HEAD + [2,1,4,3].map((n) => `T-000${n} — t${n}`).join('\n') + '\n';
  const r = run(base, ours, theirs);
  ok(r.code !== 0, 'BOTH sides re-ranking is REFUSED, not silently decided');
}
// ── the band-stripping bug, which is the reason T-0817 exists ──────────────
//
// #909, on the third time it happened: "it has now been stripped THREE times ...
// which is how six tickets the owner put at the top of QUEUE.md came to be
// sitting at line 416." These are that failure, written down so it cannot come
// back quietly.
console.log('\n== a re-rank that arrives as a NEW BAND WITH NEW TICKETS ==');
{
  // The owner writes a band at the TOP of dev with two new tickets under it. Our
  // branch has not moved a thing. The old driver dropped the band (a comment on
  // the non-ordering side) and sank both tickets to the bottom.
  const base = HEAD + 'T-0001 — old a\nT-0002 — old b\n';
  const ours = base;
  const theirs = HEAD
    + '# --- DRAIN BAND — the owner, in session: do these first\n'
    + 'T-0900 — drain one\nT-0901 — drain two\n\n'
    + 'T-0001 — old a\nT-0002 — old b\n';
  const r = run(base, ours, theirs);
  const lines = r.text.split('\n').filter((l) => l.trim());
  const at = (id) => lines.findIndex((l) => l.startsWith(id));
  ok(r.code === 0, 'it merges rather than refusing — the band is placeable');
  ok(/DRAIN BAND/.test(r.text), "the owner's band SURVIVES — it used to be dropped entirely");
  ok(at('T-0900') !== -1 && at('T-0900') < at('T-0001'),
    "…and its tickets land at the TOP where he put them, not at the bottom");
  ok(at('T-0901') === at('T-0900') + 1, '…in their own order, together');
  ok(!/MERGED IN, NOT YET PLACED/.test(r.text),
    '…and they are NOT dumped in the unplaced band, which is what used to happen');
}
{
  // The mirror image: the band arrives on OUR side while dev only closes a ticket.
  const base = HEAD + 'T-0001 — a\nT-0002 — b\n';
  const ours = HEAD + '# --- OWNER BAND\nT-0900 — new\n\nT-0001 — a\nT-0002 — b\n';
  const theirs = HEAD + 'T-0001 — a\n';
  const r = run(base, ours, theirs);
  ok(/OWNER BAND/.test(r.text) && /T-0900/.test(r.text),
    "a band on OUR side survives a dev that closed a ticket");
  ok(!/T-0002/.test(r.text), '…and their close is still honoured');
}
{
  // A ticket genuinely appended at the END of its own side has no anchor, so the
  // MERGED-IN band is still there for exactly that case.
  const base = HEAD + 'T-0001 — a\n';
  const ours = base;
  const theirs = HEAD + 'T-0001 — a\nT-0900 — appended at the end\n';
  const r = run(base, ours, theirs);
  ok(/MERGED IN, NOT YET PLACED/.test(r.text) && /T-0900/.test(r.text),
    'a ticket appended at the END still lands in the unplaced band');
}
{
  // A band the other side added ABOVE AN EXISTING ticket cannot be anchored —
  // nothing new introduces it. It must REFUSE rather than drop it silently.
  const base = HEAD + 'T-0001 — a\nT-0002 — b\n';
  const ours = HEAD + 'T-0002 — b\nT-0001 — a\n';                    // ours re-ranked
  const theirs = HEAD + 'T-0001 — a\n# --- READ THIS FIRST\nT-0002 — b\n';
  const r = run(base, ours, theirs);
  ok(r.code !== 0,
    'a band added above an EXISTING ticket is REFUSED, never silently dropped');
  ok(/READ THIS FIRST/.test(r.log),
    '…and the refusal quotes the line that would have been lost');
}
{
  // …and the counterpart: a comment the ordering side DELETED on purpose is a
  // deletion, not a loss, so it must not trip that refusal.
  const base = HEAD + '# --- STALE BAND\nT-0001 — a\nT-0002 — b\n';
  const ours = HEAD + 'T-0002 — b\nT-0001 — a\n';                    // re-ranked, band removed
  const theirs = HEAD + '# --- STALE BAND\nT-0001 — a\nT-0002 — b\n';
  const r = run(base, ours, theirs);
  ok(r.code === 0, 'a comment the ordering side deliberately removed does not refuse the merge');
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
