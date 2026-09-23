---
id: T-0721
title: Three town cards are named from an OCR misreading of an initial — 8. G. Abbot, A. 8. Perry, James I1. Gabbs — so no identity can be built from them
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 921
claimed_by: run 9/5/2026, 4:22:06 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T04:13:28.732Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33990347792
---
**Found by T-0692's coverage pass, 2026-09-04.** Three of the town's own person records are
stored under a name that contains a DIGIT, and a digit is never part of a name:

| person_id | `name` as stored | what it plainly is | sources |
|---|---|---|---|
| `abbot_8_g` | `8. G. Abbot` | `S. G. Abbot` — an S read as an 8 | `chicago_democrat_1833_1835` |
| `perry_a_8` | `A. 8. Perry` | `A. S. Perry` | `chicago_democrat_1833_1835`, `fergus_chicago_directory_1839` |
| `gabbs_james_i1` | `James I1. Gabbs` | `James H. Gabbs` — an H read as I1 | `chicago_democrat_1833_1835` |

`split_name` refuses any printed name carrying a digit, and rightly — that guard is what
stops the 1843 directory's `Reading Room (Y. M. A.), 37 Clark, 2d story` from minting an
identity called `a`. The consequence here is that these three cards can never join an
identity, never be graded by the ladder, and never be matched to another source, however
often the same man is printed elsewhere.

**This is a reading, not a repair by guess.** The letter list is the source and it is on
this project's shelf; the correct move is to go back to the printed column and read what
the initial actually is, then correct the stored name and re-run the consolidation. If the
column is genuinely illegible, say so on the card rather than picking a letter.

**Acceptance:** each of the three is settled against the source page — corrected to what
the column prints, with the reading noted and the source cited, or left with a note saying
the print cannot be read; `--coverage` shows them no longer refused for a digit; and no
identity is merged on a guessed initial.
