---
id: T-0748
title: The 1840 census continuation sheet 33SQ-GYYJ-5H read line by line, off a pale exposure that hides entries at the standard ink threshold
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0659
opened: 2026-09-05
closed: 2026-09-06
pr: 1017
claimed_by: run 9/6/2026, 8:57:45 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T02:39:56.608Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34074463758
---

The 1840 census continuation sheet 33SQ-GYYJ-5H read line by line, off a pale exposure that hides entries at the standard ink threshold.

Piece 2 of 2 of **T-0659 — The 1840 census images 26-50: continuation sheets 33SQ-GYYJ-5H and 33SQ-GYYJ-9CZ read line by line**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- The line count settled. The 28 that `coverage.json` and `pairing_key_26_50.json` carry is the count at
  the standard ink threshold, and T-0742's pass found the threshold is wrong for this leaf.
- Every line's TOTAL figure read, and the column tested against the enumerator's footed 154.
- The industry columns read per line and tested against their own footings.
- The pairing re-tested on the corrected keys, and 33SQ-GYYJ-97P's refusal either confirmed or overturned
  on the evidence.

**What T-0747's run already measured on this leaf, so this one does not start cold:**

- The column geometry is in `data/research/census_1840/pages/33SQ-GYYJ-5H.json`, measured off the FOOTER
  band rather than the header - the header band on this leaf carries printed lettering and the rules read
  off it are about 35 px out, which is a whole column's worth of error on a 65 px column.
- The enumerator's five footings are read: TOTAL 154, commerce 3, manufactures and trades 11,
  navigation of the ocean 1, learned professions 2; mining, agriculture and navigation of canals blank.
- The leaf's ink is patchy. At the module's standard 45 grey levels the TOTAL column groups into 28
  lines; at 24 it finds a further figure near y1574, and the manufactures column carries strokes near
  y1139 and y2428 that sit in TOTAL-column gaps wide enough for a line. The count is not 28.
- The sheet is recorded UNPAIRED. `pairing_key_26_50.json` refused 33SQ-GYYJ-97P (printed 211, population
  158, 30 lines) on 'population 4 short, line count 2 short'. Both halves of that refusal rest on the
  numbers this ticket re-derives.

