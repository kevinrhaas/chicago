---
id: T-0529
title: The 1840 census image 33S7-9YYJ-V2, printed 237, is a continuation sheet whose TOTAL column carries three-figure numbers and is not a household page
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0495
opened: 2026-09-03
closed: 2026-09-04
pr: 774
claimed_by: run 9/4/2026, 4:38:47 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T09:56:23.842Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33855115057
---

The 1840 census image 33S7-9YYJ-V2, printed 237, is a continuation sheet whose TOTAL column carries three-figure numbers and is not a household page.

Piece 7 of 7 of **T-0495 — The 1840 census deposit is 75 page images and 210 heads on seven printed pages are the only names read from it: images 26-50**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**What this piece is.** `33S7-9YYJ-V2` (printed 237) is filed as a continuation sheet, but its TOTAL
column carries three-figure numbers — 128, 131, 187, 117, 198, 107, 172, 154, 179, 152, 113, 201, 135,
144, 165, 161, 157, 178, 175, 181, 143 and more — where every other continuation sheet in this group
carries household counts in the single figures. Three-figure totals are what a RECAPITULATION of
divisions looks like, not a run of families.

**Why it matters.** If it is a recapitulation, it names no household, no serial may be hung on any of
its lines, and T-0504 must skip it — and it would also be a check on the division totals for the whole
enumeration, which is worth more than another 33 households.

**Acceptance:** (one demonstration, never weakened to pass)
- What the sheet is, read off the sheet and stated: recapitulation, or continuation with unusually
  large families, or something else.
- Its `what_it_is` line in `coverage.json` corrected to the finding.
- If it is a recapitulation, its figures transcribed as division totals and NOT as households, and the
  reason no line of it can carry a serial recorded where T-0504 will read it.
