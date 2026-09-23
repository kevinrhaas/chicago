---
id: T-0588
title: Norris's 1844 directory spent on the businesses layer: the firms the volume prints, dated and written where the sketch, the advertiser or Fergus 1843 puts their founding at or before 1835
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0569
opened: 2026-09-03
closed: 2026-09-03
pr: 717
claimed_by: run 9/3/2026, 1:21:18 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T18:49:22.116Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33789709731
---

Norris's 1844 directory spent on the businesses layer: the firms the volume prints, dated and written where the sketch, the advertiser or Fergus 1843 puts their founding at or before 1835.

Piece 2 of 2 of **T-0569 — Norris's 1844 directory spent on the layers: the 1835 residents validated and enriched, and the businesses written and dated**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Every 1844 firm whose founding the Historical Sketch, its own advertising card or Fergus's
  1843 directory puts at or before 1835 is written where the town's businesses are held, with
  `known_by` / `established` dates and the printing the date rests on.
- Every one of them is date-flagged; an 1844 listing alone never puts a business in the 1835 town.
- Counts in the PR: firms read, firms dated at or before 1835, firms written, firms refused.

**BOTH ITS INPUTS LANDED WHILE T-0587 WAS IN FLIGHT, AND ONE OF THEM SHORTENS THIS TICKET.**
T-0567 read the Description, the Historical Sketch and the Statistical Account as 65 dated town
findings (#710). T-0568 read the Advertising Directory card by card — 158 cards, 204 proprietors
— and reports **no founding date before 1843** anywhere in it (#712). So the advertiser, which
looked like the richest source of "established 18xx", dates nothing back to this town. What is
left to work with is the sketch's own dated statements and Fergus's 1843 directory
(`data/sources/fergus_chicago_directory_1843.json`), and the honest first move on this ticket is
to measure how many firms those two actually reach before writing any of them. A pass that
writes nothing and says why it wrote nothing closes this ticket; a pass that stretches an 1844
listing back to 1835 to have something to show does not.

The directory proper's own 65 business-kind entries remain the weakest part of T-0566's reading
(a firm whose comma falls before its ampersand reads as a person), and T-0568's cards are what
corrects them.
