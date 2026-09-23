---
id: T-0542
title: Andreas dates the third town election twice — July 1835 and 5 August 1835 — and which one the 1835 poll list is decides whether 85 men stood on the scene date
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 786
claimed_by: run 9/4/2026, 8:05:33 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T14:35:01.901Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33875911797
---

**Found by T-0493**, which read the four voter lists of 1833-1835 and was asked to settle
the 1835 poll list's date. It could not, and this is why.

The list itself prints NO DATE — just the heading `1835 Poll List`. Andreas vol. 1 dates
the third town election twice, and the two do not agree:

> The third election was held in July, 1835, and re- sulted as follows: H. Hugunin,
> President;

(the town chapter — `data/research/civic/claims/town_findings_andreas_v1.json` c006), and

> the third election of town oHicers, which occurred .Au- gust 5, 1S35

(the police chapter, c007). **The scene date is 1835-07-01.** On the first reading the
poll was taken within days of the scene; on the second, thirty-five days after it. The
owner's grading ladder makes an 1835 vote presence in Chicago, so the difference decides
what eighty-five men are worth — and T-0513's consolidation will inherit the question
unanswered unless somebody settles it.

**Two further facts that bear on it, neither decisive:**

- Of the eight men Andreas names as elected at the third election — Hugunin, W. Kimball,
  B. King, S. Jackson, E. B. Williams, F. C. Sherman, A. Loyd, George W. Dole — only three
  stand among the 85 on the poll list. That is not what one expects of a poll book for
  that election, and it may mean the list is a different poll altogether (the August
  county election is the other candidate).
- The 1833 and 1834 elections were both held in the second week of August, which is weak
  circumstantial support for the August reading against Andreas's own explicit "in July".

**And a second discrepancy in the same family, from the same reading.** Andreas says
twenty-eight men voted at the FIRST election, on 10 August 1833; the poll list prints
thirty names (c002). Either Andreas is counting the electors entitled rather than the
names enrolled, or the transcription carries the judges and clerks among the voters.
Unresolved, and it is the same act of source criticism on the same four lists.

**Where to look.** The Chicago Democrat for June-August 1835 — `data/sources/
chicago_democrat_1833_1835.json` — should print the election notice, as it printed the
1833 one that T-0493 recovered verbatim (c001: the poll at Mark Beaubien's house, 10
August, eleven o'clock, closing at one). The town's own trustee minutes, if any survive
the 1871 fire, are the other place; Andreas says most did not.

**Acceptance:**

- The 1835 poll list is dated from a source outside Andreas, or the failure is recorded as
  a negative search naming what was read.
- The reading is written into `data/sources/chicago_voter_lists_1833_1835_irad.json`'s
  `transcribes[]` entry for the 1835 list, replacing the open question standing there now.
- The 28-vs-30 discrepancy on the 1833 list is resolved or recorded the same way.
- Nothing is minted or regraded — T-0514 and T-0515 still own that.

**Links:** T-0493 (the read) · T-0513 (the consolidation that inherits this) · T-0514 ·
`data/research/civic/claims/town_findings_andreas_v1.json` c002, c006, c007 ·
`data/research/civic/search_log.json`.
