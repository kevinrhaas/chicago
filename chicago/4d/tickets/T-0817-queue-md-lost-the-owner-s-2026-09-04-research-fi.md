---
id: T-0817
title: QUEUE.md lost the owner's 2026-09-04 research-first order a second time, to a PR cut before the re-rank
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 913
claimed_by: run 9/5/2026, 2:51:42 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T19:59:51.886Z
claimed_run: null
---

QUEUE.md lost the owner's 2026-09-04 research-first order a second time, to a PR cut before the re-rank.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**It happened again, and the ledger in QUEUE.md predicted exactly how.** On 2026-09-04 the owner
said the file had been "massively reordered" and put the research-first order back, and the entry
recording that restore ends: *"HOW IT WAS LOST, because it will recur otherwise: ... PRs cut BEFORE
the re-rank each merged dev, so the stale branch was 'ours' and its old order won."*

**Measured on this run, 2026-09-05.** `origin/dev` at `d08fae3b4` carried the restored file: 415
lines, opening `# QUEUE — top is next. Text after the id is a label`. `origin/dev` at `89aaae238`,
one merge later — **PR #801 (T-0447)** — carries **321 lines** opening `# QUEUE — top is next.
Everything after the ticket id on a line is a label`, which is the **2026-08-30** revision. #801 is
a low number: a branch cut long before the re-rank, merged after it, carrying its own stale copy.
The whole research band the owner dictated on 2026-09-04 is gone from `dev` again, along with the
re-rank ledger that explains it.

**`tools/merge-queue.mjs` did its job and it was not enough.** It refused the merge — which is the
corrected behaviour the same ledger describes, "the side that actually RE-ORDERED relative to the
merge base wins, and if both did it refuses" — and that refusal reached this run, which resolved it
by hand. It never reaches a squash-merge on GitHub, because GitHub does not run this repository's
merge drivers. So the driver protects branch merges and cannot protect the thing that actually
lands.

**What this PR did about it, so the record is straight.** T-0509's merge takes the restored order,
re-appends the three tickets that arrived on `dev` in the meantime (T-0688, dev's T-0812 and
T-0802) into the MERGED-IN band, and changes no ranking of its own. That restores the owner's file
on `dev` a second time. It does not stop a third.

## The ask

1. **Gate the order, do not merge it.** `check.sh` should fail when QUEUE.md's ranking has moved
   backwards — the re-rank ledger's newest date is in the file itself and is a fingerprint a gate
   can read. A PR that carries an older ledger than its base is carrying a regression, and that is
   decidable without judging any ranking.
2. **Or take the file out of the merge.** The order is the owner's data; the ticket bodies are
   agents'. A QUEUE that is derived from a single ordering record, rather than a text file every
   branch edits, cannot be clobbered by a stale copy.
3. Whichever is chosen, say what happens to the ~14 open PRs cut before 2026-09-04 that are still
   carrying the old order — they are each one merge away from doing this again.

**Links:** the RE-RANK LEDGER in `tickets/QUEUE.md` · `tools/merge-queue.mjs` ·
`tools/merge-queue-selftest.mjs` · T-0509 (the merge that found it).
