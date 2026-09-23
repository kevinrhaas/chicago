---
id: T-0925
title: Three runs read 33S7-9YYJ-L3 on the same morning and their line counts disagree: reconcile PRs #1013, #1014 and #1015 into one reading of the leaf
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: folded into T-0957: its two residuals — a second_readings copy of #1015 and the silent claim --force — belong with the dispute they came from
needs_bake: false
closed_at: 2026-09-10T04:20:05.740Z
claimed_run: null
---

Three runs read 33S7-9YYJ-L3 on the same morning and their line counts disagree: reconcile PRs #1013, #1014 and #1015 into one reading of the leaf.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by the run that opened PR #1014, 2026-09-07.** Three steward runs claimed T-0744
within about half an hour of each other and each read 33S7-9YYJ-L3 line by line. All three
PRs are open against `dev`, all three create
`data/research/census_1840/pages/33S7-9YYJ-L3.json`, and git will let exactly one of them
land — the other two become a genuine content conflict the PR lap refuses rather than
resolves. Nothing is corrupted by that; what is lost is the disagreement, if nobody writes
it down.

**They do not agree on the ticket's headline number.**

| PR | branch | line count | the 4-vs-11 figure |
|---|---|---|---|
| #1013 | `steward/t-0744-census-l3-total` | not stated in its title | "a figure that is not 11" |
| #1014 | `steward/t-0744-census-1840-l3-read` | **27** | five of six committed 4 on T-0652's axis metric, one left unread |
| #1015 | `steward/t-0744-census-1840-l3` | **30** | not stated in its title |

**Why the count can differ honestly.** The TOTAL column's ink over the cell's own printed
rules (x 1164-1358) is 40 components, which `read_census_continuation.py` groups into 30 at
dy 45 and 55. #1014 reads those 30 groups as 27 ROWS — a two-part 5 is one figure, not two,
and two marks (12 x 14 at y 1607, 9 x 19 at y 1758) are refused as ink that is not an entry
on the 33S7-9YYJ-FJ precedent. A pass that commits the group count commits 30. So the
disagreement is about what a line IS, not about what the ink is, and it is settleable.

**This is the T-0550/T-0534 shape and it has a precedent here**: two independent readings of
one sheet, kept verbatim in `second_readings/` with a reconciliation ticket asking which is
right. Nothing should be deleted before that comparison is made.

**The cause is worth fixing separately.** `ticket.mjs claim` refuses a ticket a rival branch
carries; the run that opened #1014 passed `--force` because the ticket it had looked at first
(T-0723) had two stale branches, and carried the habit across to a ticket where the refusal
would have been right. `--force` should at least name the branch it is overriding and say
whether that branch has an open PR.

**Acceptance:**

- The three readings are compared cell by cell where they overlap, and ONE reading of
  33S7-9YYJ-L3 stands in `pages/`, with the line count stated and argued.
- Where two passes disagree on a committed figure, the disagreement is recorded — in
  `second_readings/` if the losing reading is worth keeping — and never silently dropped.
- `coverage.json` and `pairing_key_26_50.json` end consistent with whichever reading stands.
- The two PRs that do not land are closed with a comment saying which reading superseded them
  and why, not left conflicting.
- Separately: `claim --force` prints the rival branch and its PR state before it overrides.

**Links:** T-0744 (the ask) - T-0657 (its parent) - T-0656 / `pairing_key_26_50.json` (the
strip measurements all three supersede) - T-0652 / `pages/33S7-9YYJ-8D.json` (the 4-vs-11
discriminator #1014 applies) - T-0802 and T-0857 (the same family: nothing is visible between
runs before a PR merges).
