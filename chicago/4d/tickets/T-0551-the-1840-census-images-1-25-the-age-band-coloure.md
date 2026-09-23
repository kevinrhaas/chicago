---
id: T-0551
title: The 1840 census images 1-25: the age-band, coloured and industry cells of printed page 234, checked against the sheet's own column totals
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0534
opened: 2026-09-03
closed: 2026-09-03
pr: 698
claimed_by: null
blocked_on: null
needs_bake: false
---

The 1840 census images 1-25: the age-band, coloured and industry cells of printed page 234, checked against the sheet's own column totals.

Piece 2 of 2 of **T-0534 — The 1840 census images 1-25: the age-band, coloured and industry cells of printed pages 229, 231 and 234, checked against the sheets' own column totals**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- `pages/33S7-9YYJ-99F.json` (printed 234): all 31 lines, every one of the 38 age-band columns, at a
  grid fitted off the printed heading band and re-fitted every 250 px for the lean; `reading:
  scan_verified`, no IPUMS serial attached.
- Every column summed against the enumerator's own footings: 37 of 38 balance and are committed;
  column 15 (free white females 5 under 10) reads 10 against a footed 11 and is left unreconciled
  with line 17 named as the candidate.
- `coverage.json` moves the image to `names_transcribed_cells_read`; the census README carries the
  page's section.

**Closed by PR #698**, the run that had claimed the parent T-0534 before dev split it. That run also
read printed 229 and 231; dev's T-0550 (PR #697) had landed its own reading of those two pages first,
and the two disagree line by line — the second reading is preserved in `second_readings/` and
T-0559 reconciles them.
